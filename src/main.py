import os
import logging
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
# Yeni scraper'ımızı içe aktarıyoruz
from scraper import convert_via_pdf24

# Logging ayarları
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "Selam! 👋 Ben senin dosyalarını PDF'e çevirmek istiyorum. 🌸\n\n"
        "Bana Word (DOCX), PowerPoint (PPTX) veya Excel (XLSX) dosyalarını gönder, "
        "onları senin için şipşak (ve pikseli pikseline aynı) PDF'e dönüştüreyim. Hadi başlayalım! ✨"
    )
    await update.message.reply_text(welcome_msg)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    valid_extensions = ('.docx', '.doc', '.ppt', '.pptx', '.xls', '.xlsx')
    file_ext = os.path.splitext(doc.file_name)[1].lower()
    
    if file_ext not in valid_extensions:
        await update.message.reply_text("😿 Ups! Sadece DOCX, PPTX veya XLSX dosyalarını anlayabiliyorum. Başka bir şey mi gönderdin?")
        return

    # Telegram sınırı 20MB'dir, aksi takdirde get_file patlar.
    if doc.file_size > 20 * 1024 * 1024:
        await update.message.reply_text("🙀 Bu dosya benim taşıyabileceğimden biraz fazla ağır! Lütfen 20 MB'tan küçük bir dosya gönder.")
        return

    status_msg = await update.message.reply_text("✨ Dosyanı gördüm! Hemen ilgileniyorum...")

    input_path = f"/app/downloads/{doc.file_name}"
    output_path = f"/app/downloads/{os.path.splitext(doc.file_name)[0]}.pdf"

    try:
        await status_msg.edit_text("📥 Dosyanı kargocunun getirmesini bekliyorum.")
        file = await context.bot.get_file(doc.file_id)
        await file.download_to_drive(input_path)

        await status_msg.edit_text("Dosyanı fırınladım! (Bu birazcık sürebilir ☕)")
        # Burada yeni Scraping fonksiyonumuzu çağırıyoruz
        await convert_via_pdf24(input_path, output_path)

        await status_msg.edit_text("Eveet, fırından taze çıktı! Gönderiyorum yakala :D")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.UPLOAD_DOCUMENT)
        
        await update.message.reply_document(
            document=open(output_path, 'rb'),
            filename=f"{os.path.splitext(doc.file_name)[0]}.pdf",
            caption="🎉 İşte dosyanız, rica ederim."
        )
        await status_msg.delete()

    except Exception as e:
        logging.error(f"Hata: {e}")
        await status_msg.edit_text("😿 Ayy, bir şeyler ters gitti! Dosyayı elimden düşürdüm. Bugün çok sakarsam Enes'e haber verir misin?")

    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

if __name__ == '__main__':
    # PDF24'te sıraya girme ihtimaline karşı timeout sürelerini 60 saniye yapıyoruz
    app = ApplicationBuilder().token(TOKEN).connect_timeout(60.0).read_timeout(60.0).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    logging.info("Bot (Web Scraper Modu) başarıyla başlatıldı ve dinliyor...")
    app.run_polling()