import csv
import os
import requests

import genanki

back_template = 'back.template'
css_file = 'safaribooks.css'
cover_path = 'https://learning.oreilly.com/library/cover/'
deck_id = 2059400110
deck_title = 'Safaribooks'
front_template = 'front.template'
model_id = 1607392319
model_name = 'Safaribooks'
media_dir = 'media/'

fields = [
    {'name':'Note'},
    {'name':'Highlight'},
    {'name':'Title'},
    {'name':'Author'},
    {'name':'Chapter'},
    {'name':'Book URL'},
    {'name':'Chapter URL'},
    {'name':'Cover'},
    {'name':'Image'}
]


with open(css_file) as f:
    css = f.read()

with open(front_template) as f:
    front = f.read()

with open(back_template) as f:
    back = f.read()


template = [
    {
      'name': 'Card 1',
      'qfmt': front,
      'afmt': back,
    },
  ]



def read_safari_annotations(filename):
    rows = []
    with open(filename) as file:
        headers = next(file) # Skip header
        file = csv.reader(file, delimiter=',', quotechar='"') # Read CSV file
        for row in file:
            record = make_record(row)
            rows.append(record)
        return rows

class Row:
    __slots__ = (
                'title',
                'author',
                'chapter',
                'date',
                'b_url',
                'ch_url',
                'h_url',
                'highlight',
                'note',
                'tags',
                'image',
                'image_name',
                'isbn',
                'cover'
                )

    def __init__(self, title, author, chapter, date, b_url, ch_url, h_url, highlight, note):
        self.title = title
        self.author = author
        self.chapter = chapter
        self.date = date
        self.b_url = b_url
        self.ch_url = ch_url
        self.h_url = h_url
        self.highlight = highlight
        if 'url:' in note:
            self.image = note.split('url:')[-1]
            self.image_name = self.image.split('/')[-1]
            note = note.split('url:')[0]
        else:
            self.image = ''
            self.image_name = ''
        if ' #' not in note:
            print(f'Warning, tag missing in note {h_url}')
        self.note = note.split(' #')[0]
        self.tags = note.split(' #')[1].split()
        self.isbn = b_url.split('/')[-2]
        self.cover = cover_path + self.isbn

def make_record(row):
    return Row(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])

def download_media(rows):

    media_files = set()
    if not os.path.exists(media_dir):
        os.mkdir(media_dir)

    for row in rows:
        if row.image:
            file = row.image.split('/')[-1]
            filename = f'{media_dir}{row.isbn}-{file}'
            media_files.add(filename.split('/')[1])
            if not os.path.exists(filename):
                r = requests.get(row.image, allow_redirects=True)
                with open(filename, 'wb') as f:
                    f.write(r.content)
        filename = f'{media_dir}{row.isbn}.jpg'
        media_files.add(filename.split('/')[1])
        if not os.path.exists(filename):
            r = requests.get(row.cover, allow_redirects=True)
            media_files.add(filename.split('/')[1])
            with open(filename, 'wb') as f:
                f.write(r.content)
    return list(media_files)


def build_deck(rows, model_id, model_name, fields, template, css, media_files):
    deck = genanki.Deck(deck_id, deck_title)
    model = genanki.Model(
        model_id=model_id,
        name=model_name,
        fields=fields,
        templates=template,
        css=css,
        )

    for row in rows:
        cover = row.cover.split("/")[-1] + '.jpg'
        if row.image:
            image = f'{row.isbn}-{row.image_name}'
        else:
            image = ''
        note = genanki.Note(
        model=model,
        fields=[
            row.note,
            row.highlight,
            row.title,
            row.author,
            row.chapter,
            row.b_url,
            row.ch_url,
            f'<img src="{cover}" width="15%" height="15%"/>',
            f'<img src="{image}" />',
            ],
        tags=row.tags
        )
        deck.add_note(note)
    os.chdir(media_dir)
    # Generate Anki package
    my_package = genanki.Package(deck)

    # Add media files to deck
    my_package.media_files = media_files

    # Write deck to disk
    my_package.write_to_file('../test.apkg')
    os.chdir('../')

if __name__ == '__main__':
    import tracemalloc
    tracemalloc.start()
    rows = read_safari_annotations('safari-annotations-export.csv')
    media = download_media(rows)
    build_deck(rows, model_id, model_name, fields, template, css, media)
    print(tracemalloc.get_traced_memory())


