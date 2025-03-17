from functools import lru_cache
from typing import Annotated

from api.setting import AWS_REGION, SECRET_ARN_PARAMETER
from boto3.session import Session
from botocore.config import Config
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


@lru_cache()
def __get_client_for_service(service_name):
    """
    This method will return a boto3 client for the service_name given.

    :param service_name: Valid name of an AWS service
    """
    # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#overview
    session = Session(region_name=AWS_REGION)
    config = Config(region_name=AWS_REGION, signature_version="v4", retries={"max_attempts": 3, "mode": "standard",})
    available_services = session.get_available_services()
    if service_name in available_services:
        return session.client(service_name=service_name, config=config)
    raise ValueError("Requested service name ({}) is not available.".format(service_name))


@lru_cache()
def __get_ssm_parameter(parameter_name):
    try:
        client = __get_client_for_service("ssm")
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm/client/get_parameter.html
        response = client.get_parameter(Name=parameter_name, WithDecryption=True)

        if "Parameter" in response:
            return response["Parameter"]["Value"]
        else:
            raise RuntimeError(f"Parameter not found in response: {response}")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Unhandled exception raised: {repr(e)}") from e


@lru_cache()
def __get_secret_string(arn):
    try:
        client = __get_client_for_service("secretsmanager")
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager/client/get_secret_value.html
        response = client.get_secret_value(SecretId=arn)

        if "SecretString" in response:
            return response["SecretString"]
        else:
            raise RuntimeError(f"SecretString not found in response: {response}")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Unhandled exception raised: {repr(e)}") from e


api_key_secret_arn = __get_ssm_parameter(parameter_name=SECRET_ARN_PARAMETER)
api_key = __get_secret_string(arn=api_key_secret_arn)

security = HTTPBearer()


def api_key_auth(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
):
    if credentials.credentials != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key"
        )
