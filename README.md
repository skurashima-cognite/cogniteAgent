# Cognite Data Fusion File Uploader

This script provides a command-line interface to upload local files to Cognite Data Fusion (CDF). It handles authentication, file reading, and metadata assignment during the upload process.

## Prerequisites

*   Python 3.7+
*   Access to a Cognite Data Fusion project.
*   An OIDC-enabled Application in your Identity Provider (IdP) configured for use with CDF.

## Setup

1.  **Clone the repository (if applicable) or download the script.**

2.  **Install dependencies:**
    Navigate to the script's directory and install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables:**
    The script uses environment variables for authenticating with Cognite Data Fusion. Ensure the following variables are set in your environment:

    *   `CDF_PROJECT`: Your Cognite Data Fusion project name.
    *   `IDP_TENANT_ID`: The Tenant ID for your OIDC Identity Provider (e.g., Azure AD Tenant ID).
    *   `IDP_CLIENT_ID`: The Client ID of the OIDC application registered for CDF access.
    *   `IDP_CLIENT_SECRET`: The Client Secret of the OIDC application.
    *   `CDF_CLUSTER` (Optional): The CDF cluster to connect to (e.g., `api`, `westeurope-1`). Defaults to `api` if not set. The script will use this to construct URLs like `https://<CDF_CLUSTER>.cognitedata.com`.

    Example (bash):
    ```bash
    export CDF_PROJECT="my-cdf-project"
    export IDP_TENANT_ID="your-tenant-id"
    export IDP_CLIENT_ID="your-client-id"
    export IDP_CLIENT_SECRET="your-client-secret"
    # export CDF_CLUSTER="westeurope-1" # Optional
    ```

## Usage

Run the script from the command line, providing the path to the file you want to upload and any optional arguments.

```bash
python cognite_cdm_file_upload.py <file_path> [options]
```

### Arguments

*   `file_path` (Required): The local path to the file you want to upload.

### Options

*   `--external-id <external_id>`: Sets an external ID for the file in CDF. If not provided, CDF will generate one.
*   `--data-set-id <id>`: Associates the file with a specific data set in CDF. Provide the numerical ID of the data set.
*   `--mime-type <mime_type>`: Specifies the MIME type of the file (e.g., `text/csv`, `application/pdf`, `image/png`). If not provided, Cognite's API might attempt to infer it, but it's best to specify for clarity.
*   `--metadata <json_string>`: Adds custom metadata to the file. Provide a valid JSON string.
    *   Example: `--metadata '{"category": "maintenance_report", "year": "2023"}'`
*   `--source <source_name>`: Specifies the source system or script uploading the file.
    *   Default: `cognite_cdm_file_uploader_script`

### Examples

1.  **Upload a simple text file:**
    ```bash
    python cognite_cdm_file_upload.py ./my_document.txt
    ```

2.  **Upload a CSV file with an external ID and associate it with a data set:**
    ```bash
    python cognite_cdm_file_upload.py data/report.csv --external-id "report-2023-10-26" --data-set-id 1234567890
    ```

3.  **Upload a PDF file with MIME type and custom metadata:**
    ```bash
    python cognite_cdm_file_upload.py manuals/device_manual.pdf --mime-type "application/pdf" --metadata '{"device_type": "SensorX", "version": "2.1"}'
    ```

## Error Handling

*   The script prints error messages to the console if issues occur (e.g., missing credentials, file not found, upload failure).
*   Ensure your environment variables are correctly set and that the OIDC application has the necessary permissions (usually `files:read` and `files:write`) in the target CDF project.
*   Verify the file path is correct and the file is accessible.

## Contributing
(Placeholder for contribution guidelines if this were a larger project)
If you find issues or have suggestions for improvements, please open an issue or submit a pull request.
```
