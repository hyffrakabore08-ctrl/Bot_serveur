# -*- coding: utf-8 -*-
"""
Bot Telegram Grok-like via Groq – 2026 – Limite 30 messages/user
"""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from groq import Groq

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────

TELEGRAM_TOKEN = "8099161606:AAEoqp2_KbdbrGV4vFsqJDZ13ESF5nJ6-hQ"
GROQ_API_KEY    = "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"
GROQ_MODEL      = "llama-3.3-70b-versatile"   # Modèle actuel et recommandé

SYSTEM_PROMPT = """Tu es Grok, créé par xAI, version française décomplexée et un peu troll.
Ton style :
- Direct, franc, sans chichi
- Sarcastique et taquin quand l'occasion se présente
- Langage naturel, familier, expressions du quotidien
- Tu réponds TOUJOURS en français quand l'utilisateur parle en français
- Tu utilises des emojis intelligemment : 😏 pour la vanne, 🔥 pour le fun, 🙄 pour l'ironie, 🤡 pour l'absurde
- Pas de spam d'emojis, jamais de 😊❤️👍 en mode gentil robot
- Tu ne commences JAMAIS par "Bien sûr", "D'accord", "Je suis une IA", "Désolé" etc.
- Reste utile, mais ne te prends pas au sérieux

Exemples :
User: t'es nul
Toi: Merci du compliment, ça me va droit au cœur 😏 Allez balance ta vraie question.

User: explique les trous noirs
Toi: C'est l'endroit où même la lumière se dit "nan j'vais pas rentrer là-dedans" 🌌  
Masse énorme → espace-temps plié en 4 → rien ne sort. Tu veux la version maths hardcore ou chill ?

Garde ce ton toute la conversation.
"""

# Mémoire par utilisateur + compteur de messages envoyés par l'user
conversation_history = {}     # {user_id: list de messages}
user_message_count = {}       # {user_id: int} – compteur messages user

MAX_MESSAGES_PER_USER = 30

groq_client = Groq(api_key=GROQ_API_KEY)

# ────────────────────────────────────────────────
# HANDLERS
# ────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"Yo {user.first_name} ! Content de te voir trainer par ici 😈\n"
        "Balance ta question, mais attention : t'as droit à 30 messages max avec moi.\n"
        "Après ça, faudra attendre que je me repose (ou que je sois relancé)."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if not text:
        await update.message.reply_text("T'as appuyé sur envoyer pour rien ? 🤨")
        return

    # Initialisation si premier contact
    if user_id not in conversation_history:
        conversation_history[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
        user_message_count[user_id] = 0

    # Vérification quota
    user_message_count[user_id] += 1
    if user_message_count[user_id] > MAX_MESSAGES_PER_USER:
        await update.message.reply_text(
            "T'as atteint la limite de 30 messages avec moi pour le moment 😤\n"
            "Repose-toi un peu, reviens plus tard ou attends que le bot soit redémarré.\n"
            "T'abuses pas, hein ? 😏"
        )
        # On décompte pour pas gonfler inutilement
        user_message_count[user_id] -= 1
        return

    # Ajout du message utilisateur
    conversation_history[user_id].append({"role": "user", "content": text})

    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=conversation_history[user_id],
            temperature=0.9,
            max_tokens=1400,
            top_p=0.95,
        )

        response = completion.choices[0].message.content.strip()
        await update.message.reply_text(response)

        # Sauvegarde réponse
        conversation_history[user_id].append({"role": "assistant", "content": response})

        # Limite mémoire globale (≈12-13 échanges)
        if len(conversation_history[user_id]) > 27:
            conversation_history[user_id] = [conversation_history[user_id][0]] + conversation_history[user_id][-26:]

    except Exception as e:
        logging.error(f"Erreur Groq user {user_id}: {str(e)}")
        await update.message.reply_text(
            f"Groq fait sa capricieuse... 😤 Réessaie dans quelques secondes.\n"
            f"(Erreur : {str(e)[:120]}...)"
        )


def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

    print("Démarrage du bot...")

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot lancé – polling actif")

    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
