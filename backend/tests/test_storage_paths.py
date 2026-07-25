from storage import document_storage_path, get_document_url


def test_private_document_uses_store_scoped_path_and_signed_url() -> None:
    path = document_storage_path("user-uploads", "store-1", "document-1", "invoice.pdf")

    assert path == "store-1/document-1.pdf"
    assert get_document_url("user-uploads", path, signed_url="https://signed.example/file") == "https://signed.example/file"


def test_demo_document_uses_a_plain_public_url() -> None:
    path = document_storage_path("demo-assets", "store-1", "document-1", "khaata.jpg")

    assert get_document_url("demo-assets", path, supabase_url="https://project.supabase.co") == (
        "https://project.supabase.co/storage/v1/object/public/demo-assets/store-1/document-1.jpg"
    )
