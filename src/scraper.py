import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def convert_via_pdf24(input_path, output_path):
    """Playwright kullanarak PDF24 üzerinden dosyayı dönüştürür."""
    async with async_playwright() as p:
        # Docker'da çalışması için headless=True olmalı
        browser = await p.chromium.launch(headless=True)
        
        # Siteyi Türkçe açmaya zorluyoruz ki 'İNDİR' butonu çıksın
        context = await browser.new_context(
            locale='tr-TR',
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Bot korumalarına yakalanmamak için stealth
        await stealth_async(page)
        
        try:
            # 1. Sayfaya git
            await page.goto("https://tools.pdf24.org/tr/pdf-ye-cevirme", timeout=60000)
            
            # 2. Dosyayı yükle
            await page.set_input_files("input[type='file']", input_path)
            
            # 3. Yüklemenin bitmesini bekle (Sahte disabled class'ının yok olmasını bekliyoruz!)
            # Bu çok kritik, dosya sunucuya gitmeden butona basmasını engeller.
            convert_btn_selector = ".btn.action.convert:not(.disabled)"
            await page.wait_for_selector(convert_btn_selector, state="visible", timeout=90000)
            
            # Tıklama işlemini yap
            await page.locator(convert_btn_selector).click()
            
            # 4. İframe (WorkerFrame) içindeki işlemi bekle
            # PDF24 dönüştürme işlemini iframe içinde yapıyor.
            frame = page.frame_locator("iframe.workerFrame")
            
            # 5. İframe'in içindeki "İNDİR" butonunu bekle
            # Senin gönderdiğin HTML'deki yapıya tam uyumlu: span içinde İNDİR yazısı
            # (i=case insensitive, yani büyük/küçük harf fark etmez)
            download_btn = frame.locator("span:text-matches('İNDİR', 'i')").first
            await download_btn.wait_for(state="visible", timeout=120000) 
            
            # 6. Dosyayı indir ve bizim sunucuya kaydet
            async with page.expect_download(timeout=120000) as download_info:
                # Bazen span'e tıklamak yetmez, ebeveynine (butona) tıklamak gerekir
                await download_btn.locator("..").click()
                
            download = await download_info.value
            await download.save_as(output_path)
            
            return output_path
            
        except Exception as e:
            # Hata anında ekran görüntüsü almak istersen (Debug için çok işe yarar)
            # await page.screenshot(path="hata_ekrani.png")
            raise Exception(f"PDF24 Scraping Hatası: {str(e)}")
            
        finally:
            # Sunucunun RAM'i şişmesin diye tarayıcıyı hep kapatıyoruz
            await browser.close()