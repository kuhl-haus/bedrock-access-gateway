import os
from functools import lru_cache
from typing import Annotated

from boto3.session import Session
from botocore.config import Config
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.setting import DEFAULT_API_KEYS, AWS_REGION


# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#overview
def __get_default_config() -> Config:
    return Config(
        region_name=AWS_REGION,
        signature_version="v4",
        retries={
            "max_attempts": 3,
            "mode": "standard",
        },
    )


def __get_default_session() -> Session:
    return Session(region_name=AWS_REGION)


def __get_client_for_service(service_name, session: Session = None, config: Config = None):
    """
    This method will return a boto3 client for the service_name given.

    :param service_name: Valid name of an AWS service
    :param session: Optional - boto3 session
    :param config: Optional- boto3 config
    """
    if session is None:
        session = __get_default_session()
    if config is None:
        config = __get_default_config()
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


api_key_param = os.environ.get("API_KEY_PARAM_NAME")
api_key_secret_arn = os.environ.get("API_KEY_SECRET_ARN")
api_key_env = os.environ.get("API_KEY")
if api_key_param:
    api_key = __get_ssm_parameter(parameter_name=api_key_param)
elif api_key_secret_arn:
    api_key = __get_secret_string(arn=api_key_secret_arn)
elif api_key_env:
    api_key = api_key_env
else:
    api_key = DEFAULT_API_KEYS

security = HTTPBearer()


def api_key_auth(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
):
    if credentials.credentials != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key"
        )
