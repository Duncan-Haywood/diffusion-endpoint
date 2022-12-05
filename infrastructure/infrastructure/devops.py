from constructs import Construct
from aws_cdk import Stack, pipelines, Stage, CfnOutput
from infrastructure.endpoint import EndpointStack
from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_ecr as ecr
from aws_cdk.aws_ecr_assets import DockerImageAsset

OWNER_REPO = "Duncan-Haywood/diffusion-endpoint"
BRANCH = "main"


class PipelineStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, branch=BRANCH, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        source = pipelines.CodePipelineSource.git_hub(OWNER_REPO, branch)
        self.pipeline = pipelines.CodePipeline(
            self,
            "Pipeline",
            synth=pipelines.CodeBuildStep(
                "Synth",
                input=source,
                install_commands=[
                    "pip install poetry",
                    "poetry install",
                    "npm install -g aws-cdk",
                ],
                commands=[
                    "poetry run cdk synth --output ../cdk.out",
                ],
            ),
            code_build_defaults=pipelines.CodeBuildOptions(
                build_environment=codebuild.BuildEnvironment(
                    compute_type=codebuild.ComputeType.MEDIUM,
                    build_image=codebuild.LinuxBuildImage.from_asset(
                        self, "GeneralBuildImage", directory="../src/endpoint"
                    ),
                ),
                cache=codebuild.Cache.local(codebuild.LocalCacheMode.DOCKER_LAYER),
            ),
            synth_code_build_defaults=pipelines.CodeBuildOptions(
                build_environment=codebuild.BuildEnvironment(
                    compute_type=codebuild.ComputeType.MEDIUM,
                    # cache=codebuild.Cache.local(codebuild.),
                )
            ),
            asset_publishing_code_build_defaults=pipelines.CodeBuildOptions(
                build_environment=codebuild.BuildEnvironment(
                    compute_type=codebuild.ComputeType.LARGE,
                ),
                cache=codebuild.Cache.local(codebuild.LocalCacheMode.DOCKER_LAYER),
            ),
            self_mutation_code_build_defaults=pipelines.CodeBuildOptions(
                build_environment=codebuild.BuildEnvironment(
                    compute_type=codebuild.ComputeType.MEDIUM,
                )
            ),
        )
        self.pipeline.add_stage(
            EndpointStage(
                self,
                "TestStage",
                production=False,
            ),
        )
        self.pipeline.add_stage(
            EndpointStage(
                self,
                "ProdStage",
                production=True,
            ),
            pre=[pipelines.ManualApprovalStep("PromoteToProd")],
        )


class EndpointStage(Stage):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        production: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create endpoint stack
        self.app = EndpointStack(self, "EndpointStack")

        # add post processing steps with dependency graph
        upload_model_step = upload_model_step(self.app.model_bucket_name)
        upload_endpoint_step = set_endpoint_in_parameter_store(
            production, self.app.endpoint_name
        )
        integration_test_step = integration_tests()
        integration_test_step.add_step_dependency(upload_endpoint_step)
        integration_test_step.add_step_dependency(upload_model_step)

        pipelines.StackSteps(
            stack=self.app,
            pre=[unit_tests()],
            post=[upload_model_step, upload_endpoint_step, integration_test_step],
        )


## functions referenced above


def unit_tests():
    return pipelines.CodeBuildStep(
        "UnitTest",
        commands=[
            "pytest --docker-local --upload-model -n $(nproc)",
        ],
        build_environment=codebuild.BuildEnvironment(
            privileged=True,
            compute_type=codebuild.ComputeType.LARGE,
        ),
    )


def integration_tests():
    return pipelines.CodeBuildStep(
        "UnitTest",
        commands=[
            "pytest --local-integration --integration -n $(nproc)",
        ],
        build_environment=codebuild.BuildEnvironment(
            privileged=True,
            compute_type=codebuild.ComputeType.LARGE,
        ),
    )


def set_endpoint_in_parameter_store(production, endpoint_name):
    return pipelines.CodeBuildStep(
        "SetEndpointNameInParameterStore",
        commands=[
            "python ./endpoint/param_store_endpoint_name.py",
        ],
        build_environment=codebuild.BuildEnvironment(
            compute_type=codebuild.ComputeType.MEDIUM,
        ),
        env={
            "production": str(production),
        },
        env_from_cfn_outputs={
            "endpoint_name": endpoint_name,
        },
    )


def upload_model_step(model_bucket_name):
    return pipelines.CodeBuildStep(
        "UploadModel",
        commands=[
            "python ./endpoint/upload_model.py",
        ],
        build_environment=codebuild.BuildEnvironment(
            compute_type=codebuild.ComputeType.LARGE,
        ),
        env=dict(model_bucket_name=model_bucket_name),
    )


# def upload_image(image_repo_name, repository_uri, file_name, file_path):
#     return pipelines.CodeBuildStep(
#         "Image",
#         commands=[
#             "docker build --tag $IMAGE_REPO_NAME --file $FILENAME $FILE_PATH",
#             "docker tag $IMAGE_REPO_NAME $REPOSITORY_URI",
#             "docker push $REPOSITORY_URI",
#         ],
#         build_environment=codebuild.BuildEnvironment(
#             privileged=True, compute_type=codebuild.ComputeType.LARGE
#         ),
#         env=dict(
#             IMAGE_REPO_NAME=image_repo_name,
#             REPOSITORY_URI=repository_uri,
#             FILENAME=file_name,
#             FILE_PATH=file_path,
#         ),
#         cache=codebuild.Cache.local(codebuild.LocalCacheMode.DOCKER_LAYER),
#     )
