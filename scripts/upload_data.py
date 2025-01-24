"""Uploads all data to wise-loculus server"""

import logging
import os

import click
import requests
from dataclasses import dataclass
import yaml
import pandas as pd
from time import sleep
from typing import Any
import json
import re

logger = logging.getLogger(__name__)
logging.basicConfig(
    encoding="utf-8",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)8s (%(filename)20s:%(lineno)4d) - %(message)s ",
    datefmt="%H:%M:%S",
)


@dataclass
class Config:
    organism: str
    backend_url: str
    keycloak_token_url: str
    keycloak_client_id: str
    username: str
    password: str
    group_id: str
    expected_columns: list[str]


def backend_url(config: Config) -> str:
    """Right strip the URL to remove trailing slashes"""
    return f"{config.backend_url.rstrip('/')}"


def organism_url(config: Config) -> str:
    return f"{backend_url(config)}/{config.organism.strip('/')}"


def get_jwt(config: Config) -> str:
    """
    Get a JWT token for the given username and password
    """

    data = {
        "username": config.username,
        "password": config.password,
        "grant_type": "password",
        "client_id": config.keycloak_client_id,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    keycloak_token_url = config.keycloak_token_url

    response = requests.post(
        keycloak_token_url, data=data, headers=headers, timeout=600
    )
    response.raise_for_status()

    jwt_keycloak = response.json()
    return jwt_keycloak["access_token"]


def make_request(
    url: str,
    config: Config,
    params: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> requests.Response:
    """
    Generic request function to handle repetitive tasks like fetching JWT and setting headers.
    """
    jwt = get_jwt(config)
    headers = {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}
    timeout = 600
    if files:
        headers.pop("Content-Type")  # Remove content-type for multipart/form-data
        logger.info(f"Uploading files: {files}")
        response = requests.post(
            url, headers=headers, files=files, params=params, timeout=timeout
        )
    else:
        response = requests.post(
            url, headers=headers, json=json_body, params=params, timeout=timeout
        )

    if response.status_code == 423:
        logger.warning(f"Got 423 from {url}. Retrying after 30 seconds.")
        sleep(30)
        return make_request(url, config, params, files, json_body)

    if not response.ok:
        error_message = (
            f"Request failed:\n"
            f"URL: {url}\n"
            f"Status Code: {getattr(response, 'status_code', 'N/A')}\n"
            f"Response Content: {getattr(response, 'text', 'N/A')}"
        )
        logger.error(error_message)
        response.raise_for_status()
    return response


def submit(metadata, sequences, config: Config, group_id):
    url = f"{organism_url(config)}/submit"

    params = {"groupId": group_id, "dataUseTermsType": "OPEN"}
    files = {
        "metadataFile": (metadata, open(metadata, "rb")),
        "sequenceFile": (sequences, open(sequences, "rb")),
    }

    response = make_request(url, config, params=params, files=files)
    logger.debug(f"Submission response: {response.json()}")

    return response.json()


def approve(config: Config):
    """
    Approve all sequences
    """
    payload = {"scope": "ALL", "submitterNamesFilter": [config.username]}

    url = f"{organism_url(config)}/approve-processed-data"

    response = make_request(url, config, json_body=payload)

    return response.json()

def assert_string_format(s):
    # Define the regular expression for the desired format
    pattern = r'^[A-Za-z]\d+[A-Za-z\*]$'
    # Assert the string matches the pattern
    if not re.match(pattern, s):
        logger.info(f"String '{s}' does not match the required format 'letter:numbers:letter'")


def generate_dummy_fasta(config, metadata, sequence_file):
    df = pd.read_csv(metadata, sep="\t")
    if set(df.columns) != set(config.expected_columns):
        raise ValueError(
            f"Columns in metadata file {metadata} do not match expected columns"
        )
    for index, row in df.iterrows():
        print(row["submissionId"])  # Access submissionId column
        if pd.notna(row["aminoAcidMutationFrequency"]):
            print(row["aminoAcidMutationFrequency"])
            amino_acid_mutation_frequency = json.loads(row["aminoAcidMutationFrequency"])
            for key in amino_acid_mutation_frequency.keys():
                assert_string_format(key)
    with open(sequence_file, "w") as f:
        for index, row in df.iterrows():
            fasta_record = f">{row['submissionId']}\nNNN\n"
            f.write(fasta_record)

def generate_deduplicated_metadata(metadata, output_metadata):
    df = pd.read_csv(metadata, sep="\t")
    df['submissionId'] = df['submissionId'].astype(str) + df['reference'].astype(str)
    df.to_csv(output_metadata, sep="\t", index=False)


@click.command()
@click.option("--data-folder", required=True, type=click.Path(exists=True))
@click.option("--config-file", required=True, type=click.Path())
@click.option("--organism", required=True)
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
)
def main(data_folder: str, config_file: str, log_level: str, organism: str) -> None:
    logger.setLevel(log_level)

    with open(config_file, encoding="utf-8") as file:
        full_config = yaml.safe_load(file)
        relevant_config = {
            key: full_config.get(key, []) for key in Config.__annotations__
        }
        config = Config(**relevant_config)
    config.organism = organism

    logger.info(f"Config: {config}")

    for file in os.listdir(data_folder):
        if file.endswith(".tsv"):
            metadata_file = os.path.join(data_folder, file)
            sequence_file = metadata_file.replace(".tsv", ".fasta")
            deduplicated_metadata_file = metadata_file.replace(".tsv", "_deduplicated.tsv")
            generate_deduplicated_metadata(metadata_file, deduplicated_metadata_file)
            generate_dummy_fasta(config, deduplicated_metadata_file, sequence_file)
            submit(deduplicated_metadata_file, sequence_file, config, config.group_id)
    logger.info("Submitted all data. Waiting for 3 minutes before approving.")
    # sleep(3*60)
    # approve(config)
    # logger.info("Approved all sequences")


if __name__ == "__main__":
    main()
