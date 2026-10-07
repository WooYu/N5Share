"""Check local file links in the current presentation and training documents."""
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.extend(value for name, value in attrs if name == 'href' and value)


def main():
    errors, count = [], 0
    for path in [ROOT / 'README.md', ROOT / 'index.html', ROOT / 'demo/README.md', *(ROOT / 'docs').glob('*.md')]:
        text = path.read_text(encoding='utf-8')
        if path.suffix == '.html':
            parser = Links()
            parser.feed(text)
            links = parser.links
        else:
            text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
            links = re.findall(r'\]\(([^)\n]+)\)', text)
        for link in links:
            url = urlsplit(link)
            if url.scheme or url.netloc or not url.path:
                continue
            count += 1
            target = path.parent / unquote(url.path)
            if not target.exists():
                errors.append(f'{path.relative_to(ROOT)} -> {link}')
    if errors:
        raise SystemExit('Missing local links:\n' + '\n'.join(errors))
    print(f'Checked {count} local links in the presentation and documents.')


if __name__ == '__main__':
    main()
