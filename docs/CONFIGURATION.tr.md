# Yapılandırma

Tek küçük dosya: **`.env`**. Örneği kopyalayın, gerekeni değiştirin. Hiçbir şey zorunlu değil.

```bash
cp .env.example .env
```

Değerleri kolay yazın: `on` / `off`, bir sayı ya da klasör/dosya yolu (`~` çalışır; birden çok yol
virgülle ayrılır). Varsayılan için satırı silin. [English](CONFIGURATION.md)

| Ayar | Ne yazarsınız | Varsayılan | Ne yapar |
|---|---|---|---|
| `PORT` | bir sayı | `8765` | Arayüz `http://127.0.0.1:PORT` adresinde açılır |
| `OPEN_BROWSER` | `on` / `off` | `on` | Başlarken tarayıcıyı aç |
| `IDLE_MINUTES` | bir sayı | `15` | Bundan uzun boşluklar çalışma süresine sayılmaz |
| `CLAUDE_FOLDERS` | klasör(ler) | `~/.claude/projects` | Claude Code konuşmalarınızın yeri. Yedek klasörünü virgülden sonra ekleyin |
| `BACKUP_FOLDER` | bir klasör | `~/Documents/claude-session-backup/projects` | `session-archive backup` kopyaları buraya koyar |
| `APP_INDEX_FOLDER` | bir klasör | macOS konumu (hazır) | Claude masaüstü uygulamasının oturum listesi |
| `SHOW_APP` | `on` / `off` | `on` | Claude Code uygulaması ikonu |
| `SHOW_OBSIDIAN` | `on` / `off` | `on` | Obsidian kasasında başlatılan terminaller ikonu |
| `SHOW_TERMINAL` | `on` / `off` | `on` | Normal terminal ikonu |
| `SHOW_VSCODE` | `on` / `off` | `on` | VS Code ikonu |
| `SHOW_SDK` | `on` / `off` | `on` | Betik / SDK ikonu |
| `FOLDER_ICONS` | `klasör=ikon`, ... | yok | Bir klasör için kendi ikonunuz (aşağıda) |

`off`, o kaynağın kendi ikonunun olmaması demektir: `SHOW_OBSIDIAN=off` ile kasa oturumları Terminal
olarak görünür. Göreli yollar `.env` dosyasına görelidir.

## Örnekler

```ini
# başka port, tarayıcıyı açma
PORT=9000
OPEN_BROWSER=off

# ikinci bir klasörü (yedek) de oku
CLAUDE_FOLDERS=~/.claude/projects, ~/Documents/claude-yedek/projects

# VS Code ve Obsidian kullanmıyorum: ikonlarını gizle
SHOW_VSCODE=off
SHOW_OBSIDIAN=off

# ~/work altında başlayanlara "server" ikonu, ~/client-x'e kendi logom
FOLDER_ICONS=~/work=server, ~/Documents/client-x=./icons/client-x.svg
```

`FOLDER_ICONS` `klasör=ikon` çiftleri alır. İkon bir ad (`server`, `folder`, `globe`, `cloud`, `code`,
`bolt`) ya da kendi `.svg` / `.png` / `.webp` / `.jpg` dosyanızın yoludur (en çok 256 KB). Görünen
etiket klasörün adıdır. Klasör ikonları yerleşik olanların önüne geçer.

## Diğer yollar

* **Komut satırı** dosyanın üstüne yazar: `session-archive --port 9000 --no-open --projects-dir ~/x`.
* **Ortam değişkenleri** aynı adları `SESSION_ARCHIVE_` öneğiyle kullanır
  (`SESSION_ARCHIVE_PORT=9000`); böylece başka araçların `PORT`'uyla karışmaz.
* `--env-file YOL` başka bir dosyayı okur. Özel bir Claude Code config klasörü `CLAUDE_CONFIG_DIR`
  (Claude Code'un kendi değişkeni) ile alınır.

Öncelik: komut satırı > ortam > `.env` > varsayılan.

Dosyadaki bir hata başlamayı durdurur ve hangi ayarın neye çevrileceğini söyler
(`PORT: write a whole number...`). Var olmayan bir ad yalnız uyarı yazdırır.
