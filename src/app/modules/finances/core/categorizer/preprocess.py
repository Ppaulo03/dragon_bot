import random
import re
import unicodedata
import pandas as pd


def limpar_texto(texto):
    if not isinstance(texto, str):
        return ""
    texto = texto.lower()
    texto = (
        unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    )
    texto = re.sub(r"[^a-z\s]", " ", texto)
    texto = " ".join(texto.split())
    return texto


def augment_text(texto):
    palavras = texto.split()
    if not palavras:
        return texto

    escolha = random.random()
    if escolha < 0.3:
        idx = random.randint(0, len(palavras) - 1)
        if len(palavras[idx]) > 4:
            palavras[idx] = palavras[idx][:3]

    elif escolha < 0.6:
        idx = random.randint(0, len(palavras) - 1)
        palavras[idx] = palavras[idx] + random.choice(["*", "#", "-", "/"])

    elif escolha < 0.8 and len(palavras) > 1:
        random.shuffle(palavras)

    return " ".join(palavras)


def balancear_dataset(df, col=str, meta=20):
    df_lista = []

    for cat in df[col].unique():
        sub = df[df[col] == cat]
        count = len(sub)
        df_lista.append(sub)
        if count < meta:
            n_necessario = meta - count
            amostras_para_augment = sub.sample(n_necessario, replace=True)
            nova_copia = amostras_para_augment.copy()
            nova_copia["descricao"] = nova_copia["descricao"].apply(augment_text)
            df_lista.append(nova_copia)

    return pd.concat(df_lista).reset_index(drop=True)
