import extract
import transform
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, default='./data_cach/',
                    help="Path of ACE2005 data")
    parser.add_argument('--lang', type=str, help="Name of the language", default='en',
                        choices=['en', 'ar', 'zh'])
    args = parser.parse_args()


    print('\n' + '*' * 20 + lang_name[args.lang] + '*' * 20 + '\n')
    extract.main(args)

    
