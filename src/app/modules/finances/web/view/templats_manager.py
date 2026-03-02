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
import csv
import re
import chardet
from datetime import datetime

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
    # 1. Preparação e Detecção de Encoding/Delimitador
    sample_size = 4096
    buffer = await sample_csv.read(sample_size)
    if not buffer:
        return {"error": "Arquivo vazio"}

    detection = chardet.detect(buffer)
    encoding = detection["encoding"] or "utf-8"

    try:
        sample_text = buffer.decode(encoding)
    except UnicodeDecodeError:
        sample_text = buffer.decode("latin-1", errors="replace")

    try:
        dialect = csv.Sniffer().sniff(sample_text)
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";" if ";" in sample_text.split("\n")[0] else ","
    if not delimiter:
        delimiter = ";" if ";" in sample_text.split("\n")[0] else ","
    # Reset para as próximas funções lerem do início
    await sample_csv.seek(0)
    structure = await detect_structure(sample_csv, delimiter, encoding)
    mapping_indices = await infer_content(sample_csv, delimiter, encoding)
    full_context = {**structure, **mapping_indices}
    formats = await refine_formats(sample_csv, full_context, delimiter, encoding)
    await sample_csv.seek(0)
    df_sample = pd.read_csv(
        io.BytesIO(await sample_csv.read()),
        sep=delimiter,
        encoding=encoding,
        skiprows=structure["skip_rows"],
        nrows=30,
    )
    is_income_pos = await detect_income_logic(
        df_sample,
        mapping_indices["amount_column_index"],
        mapping_indices["description_column_index"],
    )

    # --- MONTAGEM DO DICIONÁRIO FINAL (Para o SQLAlchemy/Template) ---

    temp_tmp = {
        **full_context,  # Já traz skip_rows, indexes, etc.
        **formats,  # Já traz date_format, decimal_separator, counterpart_column_index        "name": sample_csv.filename.split(".")[0].replace("_", " ").title(),
        "is_income_positive": is_income_pos,
        "delimiter": delimiter,
    }
    return request.app.state.templates.TemplateResponse(
        "partials/template_fields.j2",
        {"request": request, "tmp": temp_tmp},
    )


async def infer_content(sample_csv, delimiter, encoding):
    # 1. Carregar apenas uma amostra pequena para análise (5 a 10 linhas)
    # Usamos o buffer que já temos ou lemos o início novamente
    await sample_csv.seek(0)
    content = await sample_csv.read(8192)  # 8KB é seguro

    df = pd.read_csv(
        io.BytesIO(content),
        sep=delimiter,
        encoding=encoding,
        nrows=10,
        on_bad_lines="skip",
    )

    mapping = {
        "date_idx": 0,
        "amount_idx": 1,
        "desc_idx": 2,
        "decimal": ".",
        "header": delimiter.join(df.columns.astype(str)),
    }

    scores = {i: {"date": 0, "amount": 0, "desc": 0} for i in range(len(df.columns))}

    for i, col in enumerate(df.columns):
        col_name = str(col).lower()
        column_data = df.iloc[:, i].dropna().astype(str)

        # --- HEURÍSTICA 1: Nomes de Coluna (Seu código original melhorado) ---
        if any(x in col_name for x in ["data", "date", "vencimento"]):
            scores[i]["date"] += 50
        if any(
            x in col_name for x in ["valor", "amount", "preço", "total", "lançamento"]
        ):
            scores[i]["amount"] += 50
        if any(
            x in col_name
            for x in ["desc", "histórico", "detalhe", "estabelecimento", "memo"]
        ):
            scores[i]["desc"] += 50

        # --- HEURÍSTICA 2: Teste de Conteúdo (A "Mágica") ---
        for value in column_data.head(5):
            # Teste de Data: Regex simples para formatos DD/MM ou YYYY-MM
            if re.search(r"(\d{2,4}[-/]\d{2}[-/]\d{2,4})", value):
                scores[i]["date"] += 20

            # Teste de Valor: Se tem números e talvez uma vírgula/ponto decimal
            # Remove símbolos monetários para testar
            clean_val = re.sub(r"[R\$\s\.]", "", value).replace(",", ".")
            try:
                float(clean_val)
                scores[i]["amount"] += 15
                # Detecção de separador decimal
                if "," in value and "." not in value:
                    mapping["decimal"] = ","
            except ValueError:
                # Se tem muito texto, provavelmente é descrição
                if len(value) > 15:
                    scores[i]["desc"] += 10

    # 3. Decisão baseada no vencedor de cada categoria
    mapping = {
        "date_column_index": max(scores, key=lambda x: scores[x]["date"]),
        "amount_column_index": max(scores, key=lambda x: scores[x]["amount"]),
        "description_column_index": max(scores, key=lambda x: scores[x]["desc"]),
    }
    mapping["decimal_separator"] = "."
    # Pequena lógica de decimal movida para cá para facilitar
    for i, col in enumerate(df.columns):
        if i == mapping["amount_column_index"]:
            sample = df.iloc[:, i].dropna().astype(str).to_string()
            if "," in sample and "." not in sample:
                mapping["decimal_separator"] = ","

    return mapping


async def detect_structure(sample_csv, delimiter, encoding):
    await sample_csv.seek(0)
    content = await sample_csv.read(10240)
    lines = content.decode(encoding, errors="ignore").splitlines()

    keywords = [
        "data",
        "date",
        "vencimento",
        "valor",
        "amount",
        "preço",
        "total",
        "desc",
        "histórico",
        "detalhe",
    ]

    skip_rows = 0
    header_line = ""
    for i, line in enumerate(lines[:15]):
        clean_line = line.lower()
        hits = sum(1 for word in keywords if word in clean_line)

        if hits >= 2:
            skip_rows = i
            header_line = line
            break

    original_name = sample_csv.filename
    name_parts = original_name.split("_")
    if len(name_parts) > 1:
        pattern = f"{name_parts[0]}_.*\\.{original_name.split('.')[-1]}"
    else:
        pattern = f".*\\.{original_name.split('.')[-1]}"

    return {
        "skip_rows": skip_rows,
        "expected_header": header_line,
        "csv_name_pattern": pattern,
    }


async def refine_formats(sample_csv, structure, delimiter, encoding):
    await sample_csv.seek(0)
    df = pd.read_csv(
        io.BytesIO(await sample_csv.read()),
        sep=delimiter,
        encoding=encoding,
        skiprows=structure["skip_rows"],
        nrows=20,  # Analisamos 20 linhas para ter uma base estatística boa
    )
    date_col = df.iloc[:, structure["date_column_index"]].astype(str)
    date_formats_to_test = [
        ("%d/%m/%Y", "dd/MM/yyyy"),
        ("%Y-%m-%d", "yyyy-MM-dd"),
        ("%d-%m-%Y", "dd-MM-yyyy"),
        ("%m/%d/%Y", "MM/dd/yyyy"),
        ("%d.%m.%Y", "dd.MM.yyyy"),
    ]

    detected_date_format = "dd/MM/yyyy"  # Default
    sample_date_val = date_col.iloc[0]

    for py_fmt, sql_fmt in date_formats_to_test:
        try:
            datetime.strptime(sample_date_val, py_fmt)
            detected_date_format = sql_fmt
            break
        except ValueError:
            continue
    amount_col = df.iloc[:, structure["amount_column_index"]].astype(str).to_string()
    decimal_separator = "," if amount_col.count(",") > amount_col.count(".") else "."
    counterpart_idx = None
    for i in range(len(df.columns)):
        if i in [
            structure["date_column_index"],
            structure["amount_column_index"],
            structure["description_column_index"],
        ]:
            continue
        if df.iloc[:, i].dtype == "object":
            counterpart_idx = i
            break
    return {
        "date_format": detected_date_format,
        "decimal_separator": decimal_separator,
        "counterpart_column_index": counterpart_idx,
    }


async def detect_income_logic(df, amount_idx, desc_idx):
    OUTFLOW_KEYWORDS = [
        "pagamento",
        "compra",
        "pix enviado",
        "débito",
        "saída",
        "transferência enviada",
        "tarifas",
    ]
    INFLOW_KEYWORDS = [
        "salário",
        "depósito",
        "pix recebido",
        "crédito",
        "entrada",
        "estorno",
        "rendimento",
    ]

    positive_is_outflow_votes = 0
    positive_is_inflow_votes = 0

    for _, row in df.iterrows():
        desc = str(row.iloc[desc_idx]).lower()
        # Limpamos o valor para garantir que pegamos o sinal correto
        val_str = str(row.iloc[amount_idx]).replace(".", "").replace(",", ".")
        try:
            val = float(re.sub(r"[^\d.-]", "", val_str))
        except ValueError:
            continue

        # Se o valor é positivo no CSV
        if val > 0:
            if any(k in desc for k in OUTFLOW_KEYWORDS):
                positive_is_outflow_votes += 1
            if any(k in desc for k in INFLOW_KEYWORDS):
                positive_is_inflow_votes += 1
        # Se o valor é negativo no CSV
        elif val < 0:
            if any(k in desc for k in OUTFLOW_KEYWORDS):
                positive_is_inflow_votes += (
                    1  # Voto para lógica padrão (saída = negativo)
                )
            if any(k in desc for k in INFLOW_KEYWORDS):
                positive_is_outflow_votes += 1

    return positive_is_outflow_votes <= positive_is_inflow_votes
