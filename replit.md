# PDF Download API for Papermark

## Overview
API Flask qui permet de télécharger des PDFs depuis Papermark. L'API extrait les images des pages du document et les convertit en PDF téléchargeable.

## Usage
- **Endpoint**: `GET /download?pdf=<papermark_url>&email=<email>`
- **Exemple 1**: `/download?pdf=https://www.papermark.com/view/cmj45iz65000el804x9fkmzg7&email=user@example.com`
- **Exemple 2**: `/download?pdf=https://www.papermark.com/view/cmj45gqnt0003l104j6iu9tnj&email=user@example.com`

## Comment ça marche
1. L'API utilise Playwright (navigateur automatisé) pour accéder à la page Papermark
2. Elle remplit automatiquement le formulaire d'email si requis
3. Elle capture les images des pages du document
4. Elle convertit les images en PDF avec img2pdf

## Pour télécharger sur votre téléphone
1. Ouvrez votre navigateur mobile
2. Allez à l'URL de cette API
3. Ajoutez `/download?pdf=VOTRE_URL_PAPERMARK&email=VOTRE_EMAIL`
4. Le PDF se téléchargera automatiquement

## Fichiers
- `main.py` - Serveur Flask API
- `requirements.txt` - Dépendances Python

## Dépendances
- Flask - Framework web
- Playwright - Automatisation navigateur
- img2pdf - Conversion images vers PDF
- Pillow - Traitement d'images
- Requests - Requêtes HTTP
