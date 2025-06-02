import os
import mimetypes
from cognite.client import CogniteClient, CogniteClientConfig
from cognite.client.credentials import OAuthClientCredentials
from cognite.client.data_classes import FileMetadata # Added for return type hint
from cognite.client.data_classes.data_modeling import (
    SpaceApply,
    CogniteFileApply,
    InstanceApply,
    NodeApplyInfo,
    NodeId # Added
)
from cognite.client.exceptions import CogniteNotFoundError

# --- Placeholder Variables ---
local_file_path = "./test_file_jules.txt"
cdm_space = "my_files_space"
instance_external_id = "my_document_instance_001" # External ID for the CDM instance (node)
instance_name = "My Document Example" # Name for the CogniteFile source property
instance_mime_type = "text/plain"

# --- Configuration ---
COGNITE_PROJECT = os.getenv("COGNITE_PROJECT")
CDF_CLUSTER = os.getenv("CDF_CLUSTER", "api")
COGNITE_TENANT_ID = os.getenv("COGNITE_TENANT_ID")
COGNITE_CLIENT_ID = os.getenv("COGNITE_CLIENT_ID")
COGNITE_CLIENT_SECRET = os.getenv("COGNITE_CLIENT_SECRET")
IDP_SCOPES = [f"https://{CDF_CLUSTER}.cognitedata.com/.default"]

# --- Function to Create CDM File Instance ---
def create_cdm_file_instance(
    client: CogniteClient,
    space: str,
    instance_ext_id: str, # Changed from instance_external_id to match new arg name
    file_content_ext_id: str, # New argument for the file's own external_id
    name: str,
    mime_type: str | None
) -> NodeApplyInfo | None:
    """
    Creates a data modeling instance that includes a CogniteFile source,
    linking to a file external_id.

    Args:
        client: Initialized CogniteClient.
        space: The external ID of the space for the instance.
        instance_ext_id: The external ID for the new instance (node).
        file_content_ext_id: The external ID of the actual file content in Files API.
        name: The name for the CogniteFile source's 'name' property.
        mime_type: The MIME type of the file. Guesses if None.

    Returns:
        The NodeApplyInfo of the created instance node, or None if creation fails.
    """
    actual_mime_type = mime_type # Renamed from effective_mime_type for clarity
    if not actual_mime_type:
        guessed_type, _ = mimetypes.guess_type(local_file_path)
        if guessed_type:
            actual_mime_type = guessed_type
            print(f"Guessed MIME type for '{local_file_path}': {actual_mime_type}")
        else:
            actual_mime_type = 'application/octet-stream'
            print(f"Could not guess MIME type for '{local_file_path}', defaulting to '{actual_mime_type}'.")

    # This CogniteFileApply object describes the 'file' source type and its properties.
    # It does not have its own external_id or space when used as a source for an InstanceApply.
    # The 'file_external_id' property within it points to the actual file in CDF Files API.
    cognite_file_source = CogniteFileApply(
        file_external_id=file_content_ext_id, # Links to the file in Files API
        name=name,
        mime_type=actual_mime_type
    )

    # This InstanceApply creates the actual node in the data model.
    instance_to_apply = InstanceApply(
        space=space,
        external_id=instance_ext_id, # The external_id of the node itself
        sources=[cognite_file_source] # List of sources defining this instance
    )

    try:
        print(f"Attempting to create CDM instance: space='{space}', external_id='{instance_ext_id}' "
              f"linking to file_external_id='{file_content_ext_id}'...")
        result = client.data_modeling.instances.apply(nodes=instance_to_apply)

        if result and result.nodes:
            created_node_info = result.nodes[0]
            print(f"Successfully created CDM instance: space='{created_node_info.space}', "
                  f"external_id='{created_node_info.external_id}', version='{created_node_info.version}'")
            return created_node_info
        else:
            print(f"CDM instance creation for '{instance_ext_id}' did not return expected results.")
            return None

    except Exception as e:
        print(f"Error creating CDM instance '{instance_ext_id}': {e}")
        return None

# --- Function to Upload File Content and Link to CDM Instance ---
def upload_file_content_to_cdm_instance(
    client: CogniteClient,
    local_path: str,
    file_content_ext_id: str,
    cdm_instance_space: str,
    cdm_instance_external_id: str,
    mime_type: str | None
) -> FileMetadata | None:
    """
    Uploads file content to Cognite Files API and links it to a CDM instance node.

    Args:
        client: Initialized CogniteClient.
        local_path: Path to the local file to upload.
        file_content_ext_id: External ID for the file object itself in CDF Files.
        cdm_instance_space: Space of the CDM instance to link to.
        cdm_instance_external_id: External ID of the CDM instance to link to.
        mime_type: MIME type of the file.

    Returns:
        FileMetadata object of the uploaded file, or None if upload fails.
    """
    actual_mime_type = mime_type
    if not actual_mime_type: # Guess MIME type if not provided, similar to instance creation
        guessed_type, _ = mimetypes.guess_type(local_path)
        if guessed_type:
            actual_mime_type = guessed_type
        else:
            actual_mime_type = 'application/octet-stream'

    try:
        print(f"Attempting to upload file '{local_path}' with external_id='{file_content_ext_id}'...")
        with open(local_path, 'rb') as f_content:
            file_bytes = f_content.read()

        # Note: The SDK's `source_id` parameter for files.upload_bytes expects a data modeling ID (NodeId).
        # This creates the link between the file in the Files API and the CDM Node.
        uploaded_file_metadata = client.files.upload_bytes(
            content=file_bytes,
            external_id=file_content_ext_id,
            mime_type=actual_mime_type,
            source_id=NodeId(space=cdm_instance_space, external_id=cdm_instance_external_id)
            # data_set_id can also be set here if needed
        )
        print(f"Successfully uploaded file: external_id='{uploaded_file_metadata.external_id}', "
              f"name='{uploaded_file_metadata.name}'. Linked to CDM instance: "
              f"space='{cdm_instance_space}', external_id='{cdm_instance_external_id}'.")
        return uploaded_file_metadata
    except FileNotFoundError:
        print(f"Error: Local file not found at '{local_path}'.")
        return None
    except Exception as e:
        print(f"Error uploading file '{local_path}' (ext_id: {file_content_ext_id}): {e}")
        return None

# --- Function to Ensure Space Exists ---
# (definition remains unchanged from previous step)
def ensure_space_exists(client: CogniteClient, space_external_id: str) -> bool:
    try:
        client.data_modeling.spaces.retrieve(space=space_external_id)
        print(f"Data modeling space '{space_external_id}' already exists.")
        return False
    except CogniteNotFoundError:
        print(f"Data modeling space '{space_external_id}' not found. Creating it...")
        try:
            new_space = SpaceApply(
                space=space_external_id,
                name=f"{space_external_id.replace('_', ' ').title()} Space",
                description=f"Space for {space_external_id} data models and instances."
            )
            client.data_modeling.spaces.apply(space=new_space)
            print(f"Data modeling space '{space_external_id}' created successfully.")
            return True
        except Exception as e_create:
            print(f"Error creating data modeling space '{space_external_id}': {e_create}")
            return False
    except Exception as e_retrieve:
        print(f"Error retrieving data modeling space '{space_external_id}': {e_retrieve}")
        return False

# --- Helper Functions ---
# (get_cognite_client remains unchanged)
def get_cognite_client() -> CogniteClient | None:
    if not all([COGNITE_PROJECT, COGNITE_TENANT_ID, COGNITE_CLIENT_ID, COGNITE_CLIENT_SECRET]):
        print("Error: Missing one or more Cognite credentials environment variables.")
        print("Please set COGNITE_PROJECT, COGNITE_TENANT_ID, COGNITE_CLIENT_ID, and COGNITE_CLIENT_SECRET.")
        return None
    creds = OAuthClientCredentials(
        token_url=f"https://login.microsoftonline.com/{COGNITE_TENANT_ID}/oauth2/v2.0/token",
        client_id=COGNITE_CLIENT_ID,
        client_secret=COGNITE_CLIENT_SECRET,
        scopes=IDP_SCOPES,
    )
    cnf = CogniteClientConfig(
        client_name="cognite-cdm-file-uploader-simplified",
        project=COGNITE_PROJECT,
        base_url=f"https://{CDF_CLUSTER}.cognitedata.com",
        credentials=creds,
    )
    try:
        cognite_client = CogniteClient(cnf)
        cognite_client.iam.token.inspect()
        print("Successfully connected to Cognite Data Fusion!")
        return cognite_client
    except Exception as e:
        print(f"Error connecting to Cognite Data Fusion: {e}")
        return None

if __name__ == "__main__":
    print("Attempting to initialize Cognite client...")
    cognite_client = get_cognite_client()

    if cognite_client:
        print("Cognite client initialized successfully.")

        print(f"\nChecking/Ensuring data modeling space '{cdm_space}' exists...")
        ensure_space_exists(cognite_client, cdm_space) # Call it, but no need to check 'space_was_created' for subsequent logic

        # Define an external_id for the actual file content/object in CDF Files API
        file_content_external_id = f"{instance_external_id}_content"

        print(f"\nAttempting to create CDM Instance (Node) that will reference the file content...")
        created_instance_node = create_cdm_file_instance(
            client=cognite_client,
            space=cdm_space,
            instance_ext_id=instance_external_id, # External ID of the CDM node
            file_content_ext_id=file_content_external_id, # External ID for the file in Files API
            name=instance_name,
            mime_type=instance_mime_type
        )

        if created_instance_node:
            print(f"CDM Instance Node processed. Details: Space='{created_instance_node.space}', "
                  f"ExternalID='{created_instance_node.external_id}', Version='{created_instance_node.version}'.")

            print(f"\nAttempting to upload file content and link to the CDM Instance Node...")
            # Now upload the actual file and link it using source_id
            uploaded_file_meta = upload_file_content_to_cdm_instance(
                client=cognite_client,
                local_path=local_file_path,
                file_content_ext_id=file_content_external_id,
                cdm_instance_space=created_instance_node.space, # Use space from created node
                cdm_instance_external_id=created_instance_node.external_id, # Use ext_id from created node
                mime_type=instance_mime_type # Pass original or guessed mime_type
            )

            if uploaded_file_meta:
                print(f"File content upload and linking successful for '{uploaded_file_meta.external_id}'.")
            else:
                print(f"Failed to upload and link file content for file external ID '{file_content_external_id}'.")
        else:
            print(f"Failed to create CDM Instance Node for external ID '{instance_external_id}'. "
                  "File content upload will not be attempted.")

        print(f"\nScript execution finished. Local file path used: {local_file_path}")

    else:
        print("Cognite client initialization failed. Please check credentials and configuration.")
        print("Ensure COGNITE_PROJECT, COGNITE_TENANT_ID, COGNITE_CLIENT_ID, and COGNITE_CLIENT_SECRET environment variables are set.")
