import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
import joblib
from sqlalchemy import select
from .csv_parser import Transaction
import os
import re
import random


class CategorizerService:
    def __init__(self, model_path: str = "models/finance_model.pkl"):
        self.model_path = model_path
        self.model = self._load_model()

    def _load_model(self):
        try:
            return joblib.load(self.model_path)
        except:
            return None

    def clean_description(self, text: str) -> str:
        """Limpa uma única string de descrição."""
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r"\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?", " ", text)
        text = re.sub(r"\b\d+\b", " ", text)
        text = re.sub(r"[^\w\s]", " ", text)
        tokens = [t for t in text.split() if len(t) > 2]
        return " ".join(tokens)

    def preprocess_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica a limpeza em massa e remove categorias com poucos exemplos."""
        df = df.copy()
        df["desc_clean"] = df["desc"].apply(self.clean_description)
        df = df[df["desc_clean"].str.strip() != ""]
        counts = df["category_id"].value_counts()
        valid_cats = counts[counts >= 5].index
        df = df[df["category_id"].isin(valid_cats)]
        return df

    async def train_from_db(self, db_session, df_raw: pd.DataFrame = None):
        if df_raw is None:
            # Busca dados brutos do banco
            stmt = select(Transaction).where(Transaction.category_id.is_not(None))
            result = await db_session.execute(stmt)
            txs = result.scalars().all()
            df_raw = pd.DataFrame(
                [{"desc": t.description, "category_id": t.category_id} for t in txs]
            )

        df_clean = self.preprocess_dataset(df_raw)
        if df_clean.empty:
            print("⚠️ Dataset vazio após limpeza.")
            return False

        df_enriched = self.apply_augmentation(df_clean, target_count=15)
        df_enriched["desc_clean"] = df_enriched["desc"].apply(self.clean_description)
        self.model = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 3))),
                ("clf", GradientBoostingClassifier(n_estimators=100)),
            ]
        )
        self.model.fit(df_enriched["desc_clean"], df_enriched["category_id"])
        joblib.dump(self.model, self.model_path)
        return True

    def predict(self, description: str, min_confidence: float = 0.7):
        if not self.model:
            return None

        desc_clean = self.clean_description(description)
        probs = self.model.predict_proba([desc_clean])[0]
        max_prob = max(probs)
        if max_prob < min_confidence:
            return None

        return self.model.predict([desc_clean])[0]

    async def evaluate_model(self, db_session):
        """Usa os métodos oficiais para validar a performance."""

        stmt = select(Transaction).where(Transaction.category_id.is_not(None))
        result = await db_session.execute(stmt)
        txs = result.scalars().all()
        df_raw = pd.DataFrame(
            [{"desc": t.description, "category_id": t.category_id} for t in txs]
        )

        train_df, test_df = train_test_split(df_raw, test_size=0.2, random_state=42)
        await self.train_from_db(db_session, df_raw=train_df)
        y_true, y_pred = [], []
        for _, row in test_df.iterrows():
            pred = self.predict(row["desc"])
            if pred:
                y_pred.append(pred)
                y_true.append(row["category_id"])

        # 5. Relatório
        print(
            f"📊 Cobertura com threshold de 0.7: {(len(y_pred)/len(test_df))*100:.1f}%"
        )
        print(classification_report(y_true, y_pred, zero_division=0))

    def augment_description(self, text: str) -> list[str]:
        """Gera variações sintéticas de uma descrição real."""
        variations = [text]
        words = text.split()

        if not words:
            return variations

        # Técnica 1: Injeção de ruído numérico (simulando IDs de transação)
        for _ in range(2):
            fake_id = str(random.randint(100, 9999))
            variations.append(f"{text} {fake_id}")

        # Técnica 2: Variação de prefixos bancários comuns
        prefixes = ["pix", "compra", "pagto", "venda"]
        for pref in prefixes:
            # Se a descrição já começa com um prefixo, tenta trocar
            if words[0].lower() in prefixes:
                new_text = f"{pref} {' '.join(words[1:])}"
                variations.append(new_text)
            else:
                variations.append(f"{pref} {text}")

        return list(set(variations))  # Remove duplicatas

    def apply_augmentation(
        self, df: pd.DataFrame, target_count: int = 10
    ) -> pd.DataFrame:
        """Faz o 'Oversampling' inteligente de classes minoritárias."""
        augmented_data = []

        for cat_id, group in df.groupby("category_id"):
            current_count = len(group)
            augmented_data.append(group)

            # Se a categoria tem poucos exemplos, geramos mais
            if current_count < target_count:
                needed = target_count - current_count
                for _ in range(needed):
                    # Escolhe um exemplo real aleatório para servir de base
                    source_row = group.sample(1).iloc[0]
                    new_desc = random.choice(
                        self.augment_description(source_row["desc"])
                    )

                    new_row = source_row.copy()
                    new_row["desc"] = new_desc
                    augmented_data.append(pd.DataFrame([new_row]))

        return pd.concat(augmented_data).reset_index(drop=True)
