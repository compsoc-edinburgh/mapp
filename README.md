# The Marauders App - website
This is the primary website component of [The Marauders App](https://mapp.betterinformatics.com).

## Things used
- [mapp-worker](https://github.com/compsoc-edinburgh/mapp-worker)
- Redis (for storage)
- Flask + Python

## Development

- `dc up -d redis`
- `dc build web && dc run  -v $(pwd):/code -p 9001:9000 -e FLASK_APP=map:app -e FLASK_DEBUG=1 web flask run -p 9000 -h 0.0.0.0`
- It should appear on port 9001
