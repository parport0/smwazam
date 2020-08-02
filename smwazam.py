#!/usr/bin/env python3

import io
import json
import tqdm
import sqlite3
import zipfile
import argparse
import requests
import tempfile
import itertools
import subprocess
import audiomatch.fingerprints

from bs4 import BeautifulSoup
from multiprocessing import Pool

base_url = 'https://www.smwcentral.net/?p=section&s=smwmusic&u=0&g=0&n={page}&o=date&d=desc'
sqlite_db = 'smw.db'

conn = None

def scrape_music(last_page):
    scraping_results = []
    response = requests.get(base_url.format(page=1))
    soup = BeautifulSoup(response.text, 'html.parser')
    if (last_page < 0):
        last_page = int(soup.find(id='menu').td.find_all('a')[-2].string)
    with tqdm.tqdm(total=last_page) as bar:
        for page_n in range(1, last_page + 1):
            response = requests.get(base_url.format(page=page_n))
            soup = BeautifulSoup(response.text, 'html.parser')
            for row in soup.find(id='list_content').find_all('tr')[1:]:
                columns = row.find_all("td")
                if str(columns[-1].a['href'].split('/')[-2]) == '':
                    # broken HTML at some pages
                    continue
                scraping_results.append({
                    'music_id':   str(columns[-1].a['href'].split('/')[-2]),
                    'music_link': str(columns[-1].a['href']),
                    'music_name': str(columns[0].find_all(lambda tag:tag.name == "a" and tag["href"] != "#")[0].string)
                })
            bar.update()
    return scraping_results


def db_store(music_id, music_name, music_filename, music_fingerprints):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO data VALUES (?, ?, ?, ?)",
                 (music_id, music_name, music_filename, json.dumps(music_fingerprints)))
    conn.commit()


def in_database(music_id):
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM data WHERE id = ?", (music_id,))
    return cursor.fetchone()[0]


def analyze(music_info):
    if in_database(music_info['music_id']):
        return
    request = requests.get('https:' + music_info['music_link'])
    zip_file = zipfile.ZipFile(io.BytesIO(request.content))
    for filename in zip_file.namelist():
        if filename[-4:] == '.spc':
            with tempfile.NamedTemporaryFile() as spc, tempfile.NamedTemporaryFile() as wav:
                spc.write(zip_file.read(filename))
                try:
                    subprocess.run(['./spc2wav', spc.name, wav.name], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=True)
                    fingerprints = audiomatch.fingerprints.calc(wav.name)
                    db_store(music_info['music_id'], music_info['music_name'], filename, fingerprints)
                except subprocess.CalledProcessError:
                    pass


def db_connect():
    global conn
    conn = sqlite3.connect(sqlite_db)


def scrape_and_analyze(till_page):
    conn = sqlite3.connect(sqlite_db)
    cursor = conn.cursor()
    # id is NOT unique since one archive can contain several spcs
    cursor.execute('''CREATE TABLE IF NOT EXISTS data
                   (id integer, name text, filename text, fingerprints text)''')
    conn.close()
    music = scrape_music(till_page)
    with Pool(initializer=db_connect) as pool:
        for _ in tqdm.tqdm(pool.imap_unordered(analyze, music), total=len(music)):
            pass


def compare_two(zipped):
    return (zipped[1], audiomatch.fingerprints.compare(zipped[0], json.loads(zipped[1][3])))


def find_match(needle):
    result = []
    needle_fps = audiomatch.fingerprints.calc(needle)
    with Pool() as pool:
        db_connect()
        cursor = conn.cursor()
        db_list = cursor.execute("SELECT * FROM data").fetchall()
        results = tqdm.tqdm(pool.imap_unordered(compare_two, zip(itertools.cycle([needle_fps]), db_list)), total=len(db_list))
        for x in sorted(filter(lambda x: x[1] > 0.5, results), key=lambda t: t[1]):
            result.append((x[1], x[0][0], x[0][1], x[0][2]))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='SMWCentral music fingerprinting and search') 
    subparsers = parser.add_subparsers(dest='subparser')
    parser_update = subparsers.add_parser('update', help='update the database')
    parser_update.add_argument('till_page', nargs='?', type=int, default=-1, help='scan up to this page')
    parser_match = subparsers.add_parser('match', help='find a match')
    parser_match.add_argument('filename', nargs=1, help='audio excerpt to look for, longer than 10 secs')

    args = parser.parse_args()
    if args.subparser == None:
        parser.print_help()
    elif args.subparser == 'update':
        scrape_and_analyze(args.till_page)
    else:
        matches = find_match(args.filename[0])
        for match in matches:
            print("{:.2f} | {} | {} | {}".format(match[0], match[1], match[2], match[3]))
