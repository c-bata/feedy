import asyncio
import os

import aiohttp
from bs4 import BeautifulSoup


def get_image_abs_path(domain, img_src):
    abs_path = img_src if img_src.startswith('http') else domain + img_src
    return abs_path


async def _download_and_write_image(image_url, filepath):
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            body = await response.read()
            with open(filepath, 'wb') as f:
                f.write(body)


async def _download_images(args):
    tasks = [asyncio.ensure_future(_download_and_write_image(a["url"], a["file"])) for a in args]
    results = await asyncio.gather(*tasks)
    return results


def download_image(body, domain, filename=None, directory=None, soup_find_param=None, tag_name='img'):
    if soup_find_param is None:
        soup_find_param = {}
    soup = BeautifulSoup(body, "html.parser")
    args = []
    for i, img_soup in enumerate(soup.find_all(tag_name, soup_find_param)):
        image_url = get_image_abs_path(domain, img_soup['src'])
        fn = filename.format(i=i) + "." + img_soup['src'].split('.')[-1]
        file_path = os.path.join(directory, fn) if directory else fn
        args.append({
            "url": image_url,
            "file": file_path,
        })

    loop = asyncio.get_event_loop()
    loop.run_until_complete(_download_images(args))
    loop.close()
