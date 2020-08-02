*What is this banger?* Ask no more.

## Usage

```
pip3 install -r requirements.txt
make
./smwazam.py update
./smwazam.py match file.mp3
```

The result is a reverse-sorted table of matches. The first column is the confidence; the closer the number is to 1, the more similar the songs are. The second column is an SMWCentral submission ID.

For **Twitch**, this can be used with youtube-dl. Just clip the relevant moment. It's mostly fine if someone talks over the music; it lowers the accuracy, but most of the times the results still turn out fine.

```
youtube-dl -x 'https://clips.twitch.tv/<...>'
./smwazam.py match <...>.m4a
```
