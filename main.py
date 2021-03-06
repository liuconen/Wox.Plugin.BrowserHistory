import webbrowser

from wox import Wox

import libs.browserhistory as bh


class Main(Wox):

    def query(self, key):
        splits = key.split(" ")
        force_refresh = len(splits) > 1 and splits[-1] == "-f"
        if force_refresh:
            key = "".join(splits[:-1])  # remove "-f"

        all_browsers_histories = [x for y in [v for _, v in bh.get_browserhistory(force_refresh).items()] for x in y]
        search_results = [x for x in all_browsers_histories if key in x[0] or key in x[1]]
        results = []
        for i in search_results:
            results.append({
                "Title": i[1],
                "SubTitle": i[0],
                "IcoPath": "Images/pic.png",
                "JsonRPCAction": {
                    "method": "open_url",
                    "parameters": [i[0]],
                    "dontHideAfterAction": True
                }
            })
        return results

    def open_url(self, url):
        webbrowser.open(url)


if __name__ == "__main__":
    Main()
