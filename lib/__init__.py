import os
import boto3
from lxml import etree
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv


def strip_html_tags(text: str) -> str:
    """Strip HTML tags from a string."""

    parser = etree.HTMLParser()
    tree = etree.fromstring(text, parser)
    return etree.tostring(tree, encoding="unicode", method="text")


def upload_file(filename: str):
    """Upload a file to S3."""

    load_dotenv()
    ACCESS_KEY = os.environ["AWS_ACCESS_KEY_ID"]
    SECRET_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
    s3 = boto3.client("s3", aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
    try:
        s3.upload_file(filename, "bioeco-graph", filename)
        print("Upload Successful")
    except FileNotFoundError:
        print("File not found")
    except NoCredentialsError:
        print("Credentials not available")
