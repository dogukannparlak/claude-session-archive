# Yapılandırma

Hiçbir ayar yapmadan çalışır. Kurulumunuz farklıysa (başka klasörler, başka araçlar, ek kaynaklar)
üç yerden değiştirebilirsiniz. [English](CONFIGURATION.md)

| Katman | Dosya | Ne için |
|---|---|---|
| Komut satırı | `--port`, `--projects-dir` gibi bayraklar | tek seferlik çalıştırma |
| Ortam | gerçek değişkenler ya da `.env` dosyası (`.env.example`) | makineye özel yol ve port |
| Config dosyası | `session-archive.json` (`session-archive.example.json`) | yollar **ve** kaynak/ikon listesi |

Her ayar için öncelik: **bayrak > ortam > `.env` > config dosyası > varsayılan**.

## Config dosyası nerede aranır

İlk bulunan geçerlidir: `--config YOL`, `$SESSION_ARCHIVE_CONFIG`, `./session-archive.json`,
`$XDG_CONFIG_HOME/session-archive/config.json` (`~/.config/...`). Kullanılan dosyanın yolu başlarken
yazılır. `.env` geçerli klasörden okunur (ya da `--env-file YOL`). `session-archive.json` ve `.env`
git'e girmez; `*.example` dosyaları girer.

Tüm varsayılanları yazılı bir dosya üretmek için:

```bash
session-archive print-config > session-archive.json
```

Bilinmeyen anahtarlar hatadır (yazım hataları sessizce geçmesin); `_` ile başlayan anahtarlar
yok sayılır, yorum için kullanın (`"_comment": "..."`). Göreli yollar config dosyasına görelidir.

## Ayarlar

| Config anahtarı | Ortam değişkeni | Varsayılan | Anlamı |
|---|---|---|---|
| `port` | `SESSION_ARCHIVE_PORT` | `8765` | `127.0.0.1` üzerindeki port |
| `open_browser` | `SESSION_ARCHIVE_OPEN_BROWSER` | `true` | Başlarken tarayıcıyı aç |
| `idle_minutes` | `SESSION_ARCHIVE_IDLE_MINUTES` | `15` | Bundan uzun boşluklar aktif süreye sayılmaz |
| `projects_dirs` | `SESSION_ARCHIVE_PROJECTS_DIRS` | `$CLAUDE_CONFIG_DIR/projects` ya da `~/.claude/projects` | Kayıt klasörleri; yedek klasörünü de buraya ekleyin |
| `app_index` | `SESSION_ARCHIVE_APP_INDEX` | macOS: `~/Library/Application Support/Claude/claude-code-sessions` | Masaüstü uygulamasının oturum dizini (`backup` kullanır) |
| `backup_dir` | `SESSION_ARCHIVE_BACKUP_DIR` | `~/Documents/claude-session-backup/projects` | `session-archive backup` hedefi |
| `sources` | (yalnız config dosyası) | aşağıdaki beş kaynak | Bir oturumun nereden geldiğini gösteren etiket, ikon ve kurallar |

Ortam değişkenlerindeki listeler `PATH` gibi ayrılır: macOS/Linux'ta `:`, Windows'ta `;`.

### Makinenizde farklı yollar

```json
{
  "projects_dirs": ["~/.claude/projects", "/mnt/yedek/claude/projects"],
  "app_index": ["~/Library/Application Support/Claude/claude-code-sessions"],
  "backup_dir": "/mnt/yedek/claude/projects"
}
```

Özel bir Claude Code config klasörü kullanıyorsanız `CLAUDE_CONFIG_DIR` (Claude Code'un kendi
değişkeni) ayarlayın; kayıt klasörü onu izler.

## Kaynaklar: etiket, ikon ve kurallar

*Kaynak*, bir oturumun nereden başladığını ve nasıl gösterileceğini söyler. Her oturum kurallara
**sırayla** sorulur; **ilk eşleşen kazanır**. Hiçbiriyle eşleşmeyen oturum `other` olur (her zaman
var olan yerleşik yedek; tanımlamayın).

Neyi değiştirdiğinizi görmeniz için varsayılanlar:

| anahtar | İkon | Eşleşme |
|---|---|---|
| `desktop` | Claude logosu | `entrypoint: claude-desktop` |
| `obsidian` | Obsidian logosu | `entrypoint: cli` **ve** çalışma klasörü `.obsidian` içeren bir klasörde |
| `terminal` | `>_` | `entrypoint: cli` |
| `vscode` | VS Code logosu | `entrypoint: claude-vscode` |
| `sdk` | fiş | `entrypoint: sdk-cli`, `sdk-ts`, `sdk-py` |

`obsidian`, `terminal`'den önce geldiği için kasa oturumları öne geçer. Listeyi düzenleyerek kural
**ekleyin, çıkarın ya da sıralayın**: config'inizde `sources` varsa varsayılanların *yerine geçer*;
dışarıda bıraktığınız kaynak kaybolur. `session-archive print-config` ile başlayın.

Bir kaynak:

```json
{
  "key": "work",
  "label": {"en": "Work server", "tr": "İş sunucusu"},
  "icon": "server",
  "match": {"cwd_prefix": ["/srv/work", "~/work"]}
}
```

| Alan | Anlamı |
|---|---|
| `key` | Harf, rakam, `-`, `_`. Benzersiz. `other` olamaz. |
| `label` | Metin ya da `{dil: metin}` (arayüz önce kendi dilini, sonra İngilizceyi seçer). |
| `icon` | Yerleşik bir ad (aşağıda). |
| `icon_file` | `icon` yerine kendi görseliniz: `.svg`, `.png`, `.webp`, `.jpg`, en çok 256 KB. Config dosyasına göre. |
| `match` | En az bir alan. Verilen **tüm** alanlar sağlanmalı; liste öğeleri alternatiftir. |

`match` alanları:

| Alan | Şu durumda doğru |
|---|---|
| `entrypoint` | kaydın `entrypoint` değeri listedekilerden biri (`cli`, `claude-desktop`, `claude-vscode`, `sdk-cli`, ...) |
| `cwd_has` | çalışma klasörü **ya da bir üst klasörü** bu adlardan birini içeriyor (klasör ya da dosya, örn. `.obsidian`, `.git`) |
| `cwd_prefix` | çalışma klasörü bu yollardan biriyle başlıyor (`~` açılır) |
| `cwd_contains` | çalışma klasörü bu metinlerden birini içeriyor |

Yerleşik ikonlar: `claude`, `obsidian`, `vscode` (ürün logoları, bkz. [NOTICE.md](../NOTICE.md)),
`terminal`, `sdk`, `server`, `folder`, `globe`, `cloud`, `code`, `bolt`, `other` (genel çizimler).

### Örnekler

`client-x` adlı bir klasördeki her şeyi kendi logonuzla ayrı kaynak yapın:

```json
{"key": "client-x", "label": "Client X", "icon_file": "icons/client-x.svg", "match": {"cwd_contains": ["/client-x/"]}}
```

Obsidian'ı, `.obsidian` olan her klasör yerine yalnız kendi kasanızdan başlayanlar için ayırın:

```json
{"key": "obsidian", "icon": "obsidian", "label": "Obsidian", "match": {"entrypoint": ["cli"], "cwd_prefix": ["~/Documents/Kasam"]}}
```

Obsidian kaynağını tümden kaldırmak için girdisini silin; o oturumlar `terminal` olur.

Notlar:
- Obsidian terminal eklentisi normal bir `claude` başlatır; oturumları yalnız çalıştıkları yere göre
  tanınır. Kuralların çalışma klasörüne bakabilmesinin nedeni budur.
- Klasörler, oturum özeti oluşturulurken denetlenir; `cwd_has` oturum başına birkaç dosya sistemi
  sorgusu demektir (özetler önbelleğe alınır).
- Geçersiz config başlamayı durdurur; mesaj dosyayı ve alanı adıyla söyler.
