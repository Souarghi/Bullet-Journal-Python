# Image de base Python
FROM python:3.12-slim

# Évite les fichiers .pyc et rend les logs immédiats
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Installe les dépendances en premier (mise en cache de cette couche)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie tous les fichiers du répertoire
COPY . .

# Commande par défaut : lance le menu du Bullet Journal
CMD ["python", "-m", "bujo"]