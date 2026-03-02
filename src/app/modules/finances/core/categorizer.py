import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
import joblib
from sqlalchemy import select  # Para salvar o modelo treinado
from .csv_parser import Transaction
import os


class CategorizerService:
    def __init__(self, model_path: str = "models/finance_model.pkl"):
        self.model_path = model_path
        self.model = self._load_model()

    def _load_model(self):
        try:
            return joblib.load(self.model_path)
        except:
            return None

    async def train_from_db(self, db_session):
        """Busca dados históricos e treina o modelo."""
        # Busca transações que já foram categorizadas (exemplo: pelo usuário)
        stmt = select(Transaction).where(Transaction.category_id.is_not(None))
        result = await db_session.execute(stmt)
        txs = result.scalars().all()

        if len(txs) < 10:  # Mínimo de amostras para não dar overfit
            print("⚠️ Dados insuficientes para treinamento.")
            return

        # Prepara o DataFrame
        data = [
            {"desc": t.description, "cat": t.category_id, "ent": t.entity} for t in txs
        ]
        df = pd.DataFrame(data)

        # Pipeline: Vetorização -> Classificação
        pipeline = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
                ("clf", RandomForestClassifier(n_estimators=100)),
            ]
        )

        # Treino para Categoria
        pipeline.fit(df["desc"], df["cat"])
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(pipeline, self.model_path)
        self.model = pipeline
        print("🎯 Modelo treinado e salvo com sucesso!")

    def predict(self, description: str):
        """Retorna a predição se o modelo existir e tiver confiança."""
        if not self.model or not description:
            return None

        try:
            # Você pode usar model.predict_proba para checar a confiança
            prediction = self.model.predict([description])[0]
            return prediction
        except:
            return None

    async def evaluate_model(self, db_session):
        """Treina temporariamente e exibe métricas detalhadas."""
        stmt = select(Transaction).where(Transaction.category_id.is_not(None))
        result = await db_session.execute(stmt)
        txs = result.scalars().all()

        if len(txs) < 20:
            print("⚠️ Dados insuficientes para avaliação.")
            return

        df = pd.DataFrame([{"desc": t.description, "cat": t.category_id} for t in txs])

        counts = df["cat"].value_counts()

        # Mantém apenas categorias que tenham pelo menos 2 exemplos
        valid_categories = counts[counts >= 2].index
        df_filtered = df[df["cat"].isin(valid_categories)].copy()

        if df_filtered.empty:
            print(
                "⚠️ Nenhuma categoria possui exemplos suficientes (min: 2) para avaliação estratificada."
            )
            return
        # 1. Split: 80% treino, 20% teste
        X_train, X_test, y_train, y_test = train_test_split(
            df_filtered["desc"],
            df_filtered["cat"],
            test_size=0.2,
            random_state=42,
            stratify=df_filtered["cat"],
        )

        # 2. Treino rápido para validação
        pipeline = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
                (
                    "clf",
                    RandomForestClassifier(n_estimators=100, class_weight="balanced"),
                ),
            ]
        )
        pipeline.fit(X_train, y_train)

        # 3. Predição no set de teste
        y_pred = pipeline.predict(X_test)

        # 4. Relatório
        print("\n📊 --- RELATÓRIO DE PERFORMANCE DO MODELO ---")
        print(classification_report(y_test, y_pred))
        print("---------------------------------------------\n")
