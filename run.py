import argparse

from toad import create_app

def parse_args():
    parser = argparse.ArgumentParser(description="Toad Flask backend")
    parser.add_argument("--seed", help="Folder location containing JSON files to hydrate the database", required=False)
    return parser

if __name__ == '__main__':
    parser = parse_args()
    args = parser.parse_args()

    if args.seed:
        print(f'Running app with seed = {args.seed}')
        app = create_app(seed=args.seed) 
    else:
        app = create_app() 
    app.run(debug=True)
