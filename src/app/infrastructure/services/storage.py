import aioboto3
from botocore.exceptions import ClientError
from loguru import logger
from typing import Optional, List

from app.config import settings


class StorageService:
    _instance: Optional["StorageService"] = None

    def __new__(cls):
        """Implementação Singleton para evitar múltiplas sessões."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.session = aioboto3.Session()
        self.active = bool(settings.BUCKET_ENDPOINT and settings.BUCKET_ACCESS_KEY)

        if not self.active:
            logger.warning(
                "StorageService: Credenciais S3/MinIO não configuradas. Serviço inativo."
            )

        self._initialized = True

    def _get_client_args(self) -> dict:
        """Centraliza as configurações de conexão com o Provider (AWS/MinIO/Cloudflare)."""
        return {
            "service_name": "s3",
            "endpoint_url": settings.BUCKET_ENDPOINT,
            "aws_access_key_id": settings.BUCKET_ACCESS_KEY,
            "aws_secret_access_key": settings.BUCKET_SECRET_KEY,
            "region_name": settings.BUCKET_REGION or "us-east-1",
        }

    async def setup(self):
        """
        Método de inicialização assíncrona.
        Deve ser chamado no 'lifespan' do FastAPI para garantir que o bucket existe.
        """
        if not self.active:
            return

        try:
            async with self.session.client(**self._get_client_args()) as s3:
                try:
                    await s3.head_bucket(Bucket=settings.BUCKET_NAME)
                    logger.info(
                        f"StorageService: Conectado ao bucket '{settings.BUCKET_NAME}'."
                    )
                except ClientError:
                    logger.info(
                        f"StorageService: Bucket '{settings.BUCKET_NAME}' não encontrado. Criando..."
                    )
                    await s3.create_bucket(Bucket=settings.BUCKET_NAME)
        except Exception as e:
            logger.error(f"Erro ao inicializar conexão com Storage: {e}")
            self.active = False

    async def upload_file(
        self, file_name: str, data: bytes, content_type: str
    ) -> Optional[str]:
        """Faz o upload de bytes e retorna o nome do arquivo/chave se sucesso."""
        if not self.active:
            return None

        try:
            async with self.session.client(**self._get_client_args()) as s3:
                await s3.put_object(
                    Bucket=settings.BUCKET_NAME,
                    Key=file_name,
                    Body=data,
                    ContentType=content_type,
                )
                return file_name
        except Exception as e:
            logger.error(f"Falha no upload do arquivo '{file_name}': {e}")
            return None

    async def get_presigned_url(self, file_key: str, expires_in: int = 3600) -> str:
        """Gera uma URL temporária para acesso público ao arquivo."""
        if not self.active:
            return ""

        try:
            async with self.session.client(**self._get_client_args()) as s3:
                return await s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": settings.BUCKET_NAME, "Key": file_key},
                    ExpiresIn=expires_in,
                )
        except Exception as e:
            logger.error(f"Erro ao gerar URL assinada para '{file_key}': {e}")
            return ""

    async def delete_file(self, file_key: str) -> bool:
        """Remove um objeto do bucket de forma definitiva."""
        if not self.active:
            return False

        try:
            async with self.session.client(**self._get_client_args()) as s3:
                await s3.delete_object(Bucket=settings.BUCKET_NAME, Key=file_key)
                return True
        except Exception as e:
            logger.error(f"Erro ao deletar arquivo '{file_key}': {e}")
            return False

    async def list_all_files(self, prefix: str = "") -> List[str]:
        """Lista todas as chaves (keys) presentes no bucket com um prefixo opcional."""
        if not self.active:
            return []

        files = []
        try:
            async with self.session.client(**self._get_client_args()) as s3:
                paginator = s3.get_paginator("list_objects_v2")
                async for page in paginator.paginate(
                    Bucket=settings.BUCKET_NAME, Prefix=prefix
                ):
                    if "Contents" in page:
                        files.extend([obj["Key"] for obj in page["Contents"]])
            return files
        except Exception as e:
            logger.error(f"Erro ao listar objetos no bucket: {e}")
            return []

    async def get_item_content(self, file_key: str) -> Optional[bytes]:
        """Recupera o conteúdo de um arquivo como bytes."""
        if not self.active:
            return None

        try:
            async with self.session.client(**self._get_client_args()) as s3:
                response = await s3.get_object(
                    Bucket=settings.BUCKET_NAME, Key=file_key
                )
                return await response["Body"].read()
        except Exception as e:
            logger.error(f"Erro ao obter conteúdo do arquivo '{file_key}': {e}")
            return None
