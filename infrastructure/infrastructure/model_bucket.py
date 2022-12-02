from aws_cdk import aws_s3 as s3
from aws_cdk import Stack, RemovalPolicy
from constructs import Construct


class ModelBucketStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        # model bucket for hosting the model files
        model_bucket = s3.Bucket(
            self,
            "ModelBucket",
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY,
        )
        # name of model bucket
        self.model_bucket_name = model_bucket.bucket_name
