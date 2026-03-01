from fastapi import (
    APIRouter,
    File,
    Request,
    Form,
    Depends,
    HTTPException,
    Response,
    UploadFile,
)
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from sqlalchemy import delete

from app.modules.finances.database.client import get_db_session

from app.modules.finances.database.models import Template
import pandas as pd
import io

router = APIRouter(prefix="/templates")


@router.get("/")
async def list_templates(request: Request, db: AsyncSession = Depends(get_db_session)):
    res = await db.execute(select(Template).order_by(Template.name))
    templates = res.scalars().all()
    return request.app.state.templates.TemplateResponse(
        "templates.j2", {"request": request, "templates": templates}
    )


@router.get("/edit/{tmp_id}")
@router.get("/new")
async def template_form(
    request: Request,
    tmp_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db_session),
):
    template = None
    if tmp_id:
        res = await db.execute(select(Template).filter_by(id=tmp_id))
        template = res.scalar_one_or_none()

    return request.app.state.templates.TemplateResponse(
        "partials/template_form.j2", {"request": request, "tmp": template}
    )


@router.post("/save")
async def save_template(
    name: str = Form(...),
    template_id: Optional[int] = Form(None),
    csv_name_pattern: Optional[str] = Form(None),
    expected_header: Optional[str] = Form(None),
    delimiter: str = Form(";"),
    skip_rows: int = Form(1),
    date_column_index: int = Form(...),
    description_column_index: int = Form(...),
    amount_column_index: int = Form(...),
    counterpart_column_index: Optional[str] = Form(
        None
    ),  # Recebe como string para tratar vazio
    date_format: str = Form("%d/%m/%Y"),
    decimal_separator: str = Form(","),
    is_income_positive: str = Form("true"),
    db: AsyncSession = Depends(get_db_session),
):
    # Tratamento de tipos específicos
    is_pos = is_income_positive.lower() == "true"

    # Converte counterpart_index apenas se houver valor
    cp_index = (
        int(counterpart_column_index)
        if counterpart_column_index and counterpart_column_index.strip() != ""
        else None
    )

    if template_id:
        res = await db.execute(select(Template).filter_by(id=template_id))
        tmp = res.scalar_one_or_none()
        if not tmp:
            raise HTTPException(status_code=404, detail="Template não encontrado")

        # Atualização dos campos
        tmp.name = name
        tmp.csv_name_pattern = csv_name_pattern
        tmp.expected_header = expected_header
        tmp.delimiter = delimiter
        tmp.skip_rows = skip_rows
        tmp.date_column_index = date_column_index
        tmp.description_column_index = description_column_index
        tmp.amount_column_index = amount_column_index
        tmp.counterpart_column_index = cp_index
        tmp.date_format = date_format
        tmp.decimal_separator = decimal_separator
        tmp.is_income_positive = is_pos
    else:
        # Criação
        tmp = Template(
            name=name,
            csv_name_pattern=csv_name_pattern,
            expected_header=expected_header,
            delimiter=delimiter,
            skip_rows=skip_rows,
            date_column_index=date_column_index,
            description_column_index=description_column_index,
            amount_column_index=amount_column_index,
            counterpart_column_index=cp_index,
            date_format=date_format,
            decimal_separator=decimal_separator,
            is_income_positive=is_pos,
        )
        db.add(tmp)

    await db.commit()
    return RedirectResponse(url="/finance/templates", status_code=303)


@router.delete("/{tmp_id}")
async def delete_template(tmp_id: int, db: AsyncSession = Depends(get_db_session)):
    try:
        await db.execute(delete(Template).where(Template.id == tmp_id))
        await db.commit()
        return Response(headers={"HX-Redirect": "/finance/templates"})
    except Exception:
        await db.rollback()
        return Response(
            status_code=500,
            content="Erro ao deletar template. Verifique se há contas usando ele.",
        )


@router.post("/analyze-csv")
async def analyze_csv(request: Request, sample_csv: UploadFile = File(...)):
    # 1. Ler o início do arquivo para detectar estrutura
    content = await sample_csv.read()
    # Tenta detectar o delimitador (pode ser expandido com csv.Sniffer)
    text_content = content.decode("utf-8", errors="ignore")
    first_line = text_content.split("\n")[0]
    delimiter = ";" if ";" in first_line else ","

    # 2. Carregar no Pandas para análise (apenas as primeiras 5 linhas)
    df = pd.read_csv(io.BytesIO(content), sep=delimiter, nrows=5)

    # 3. Lógica de Inferência (A "mágica")
    mapping = {
        "date_idx": 0,
        "amount_idx": 1,
        "desc_idx": 2,
        "header": delimiter.join(df.columns),
    }

    for i, col in enumerate(df.columns):
        col_name = str(col).lower()

        # Tenta achar Data
        if any(x in col_name for x in ["data", "date", "vencimento"]):
            mapping["date_idx"] = i
        # Tenta achar Valor
        elif any(x in col_name for x in ["valor", "amount", "preço", "total"]):
            mapping["amount_idx"] = i
        # Tenta achar Descrição
        elif any(
            x in col_name for x in ["desc", "histórico", "detalhe", "estabelecimento"]
        ):
            mapping["desc_idx"] = i

    # Criamos um objeto "fake" de Template para preencher o formulário
    # Os campos que não detectamos, o user ajusta na mão
    temp_tmp = {
        "name": sample_csv.filename,
        "delimiter": delimiter,
        "expected_header": mapping["header"],
        "date_column_index": mapping["date_idx"],
        "amount_column_index": mapping["amount_idx"],
        "description_column_index": mapping["desc_idx"],
        "skip_rows": 1,  # Padrão
        "date_format": "%d/%m/%Y",  # Padrão
        "decimal_separator": "," if delimiter == ";" else ".",
    }

    # 4. Retorna o formulário preenchido
    return request.app.state.templates.TemplateResponse(
        "partials/template_fields.j2",  # Vamos quebrar o form em pedaços para o HTMX
        {"request": request, "tmp": temp_tmp},
    )
