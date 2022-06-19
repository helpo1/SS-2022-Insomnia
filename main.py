import datetime
import fileinput
import requests

offers_file = 'offers.txt'
insomnia_url = 'https://www.gog.com/en/insomnia'
catalog_url = 'https://catalog.gog.com/v1/catalog'


def get_insomnia_info(url=insomnia_url):
    response = requests.get(url)
    return response.json()


def get_filtered_results(url=catalog_url):
    response = get_insomnia_info()

    if response['upcomingInsomniaExists']:
        tags = response['upcomingInsomniaData']['tags']
        tag_codes = {tag['slug'] for tag in tags}
        tag_codes = ','.join(tag_codes)
        params = {
            'tags': 'is:' + tag_codes,
            'order': 'asc:title',
            'productType': 'in:game,pack,dlc,extras',
            'locale': 'en-US',
            'currencyCode': 'USD'
        }
        response = requests.get(url, params=params)
        return response.json()['products']

    else:
        return 'No (public) upcoming offer'


def read_last_offer():
    # remove all blank lines from file
    for line in fileinput.FileInput(offers_file, inplace=1):
        if line.rstrip():
            print(line, end='')

    # find last offer's line position from end of file & its contents
    with open(offers_file, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
        try:
            neg_counter = -1
            last_line = all_lines[neg_counter]
            while last_line == '\n':
                neg_counter -= 1
                last_line = all_lines[neg_counter]
        except IndexError:
            print('WARNING: No past offers found in ' + offers_file + '\n')
            return 0, ''

    return neg_counter, last_line


def append_current_offer(insomnia_info=None):
    if insomnia_info is None:
        raise ValueError('No Insomnia offer info available')

    offer = insomnia_info['insomniaDetails']
    product = offer['product']

    neg_counter, last_line = read_last_offer()
    if '[url=' + product['store'] + ']' in last_line:
        # print('Product already in offers, returning')
        return
    else:
        # print('Product not in offers, adding')
        pass

    if not neg_counter < 0:
        counter = 1
    else:
        counter = int(last_line.split('. ')[0]) + 1

    # append current offer to file
    with open(offers_file, 'a', encoding='utf-8') as f:
        f.write('\n%d. [b][url=%s]%s[/url][/b] [%s %s -> %s (-%s%%), ?/%s sold]\n' % (
            counter, product['store'], product['title'], offer['currencyCode'], offer['basePrice'],
            offer['finalPrice'], offer['discount'], offer['maxQuantity']))


def print_offer_details(upcoming_offers=None):
    print('---')

    # get UTC time from timestamp
    timestamp = get_insomnia_info()['insomniaDetails']['dateStart']
    utc_time = datetime.datetime.utcfromtimestamp(timestamp)
    utc_time = utc_time.strftime('%Y-%m-%d %H:%M')

    print('[b]Insomnia deals so far '
          '+ [url=' + insomnia_url + ']predicted[/url] upcoming (%s UTC):[/b]' % utc_time)

    neg_counter, last_line = read_last_offer()
    if not neg_counter < 0:
        last_line = '0. '
    else:
        # print past offers
        print('\n[u]Past:[/u]')
        with open(offers_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            for line in all_lines[:neg_counter]:
                print(line.rstrip('\n'))

        # print current (last) offer
        print('\n[u]Current:[/u]')
        print(all_lines[neg_counter].rstrip('\n'))

    counter = int(last_line.split('. ')[0]) + 1

    # print upcoming offer
    print('\n[u]Upcoming:[/u]')
    if upcoming_offers is None or len(upcoming_offers) < 1:
        print('No upcoming offer guesses available')
    else:
        if len(upcoming_offers) > 1:
            print('!! Multiple possible upcoming offer guesses available !!')
        for offer in upcoming_offers:
            print('%d. [b][url=%s]%s[/url][/b] [%s -> $? (-?%%), ?/? sold]' % (
                counter, 'https://www.gog.com/en/game/'+offer['slug'].replace('-', '_'),
                offer['title'], offer['price']['base']))

    print('---')


if __name__ == '__main__':
    # ensure file existence
    open(offers_file, 'a+').close()

    append_current_offer(get_insomnia_info())
    print_offer_details(get_filtered_results())
