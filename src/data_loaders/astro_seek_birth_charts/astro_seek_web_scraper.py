import re
import time

import pandas as pd

from data_loaders.utils import get_beauiful_soup_object_from_base_url, pretty_print


class AstroSeekWebScraper:
    def __init__(self, astro_seek_base_url):
        self._astro_seek_base_url = astro_seek_base_url

    def load_raw_celebrity_astro_seek_data(self, occupations_not_considered):
        soup = get_beauiful_soup_object_from_base_url(self._astro_seek_base_url)
        occupation_type_urls = self._get_hrefs_for_occupation_types(soup)
        astro_chart_data_for_people_by_occupation_type = []
        occupation_urls_to_scrape = [
            url for url in occupation_type_urls if not any(elem in url for elem in occupations_not_considered)
        ]

        for occupation_type_url in occupation_urls_to_scrape:
            start_time = time.time()

            occupation = occupation_type_url.split('/')[-1]
            print(f"Collecting data for {occupation}...")

            hrefs_for_famous_people_in_occupation_url = self._get_hrefs_for_famous_people_by_occupation_type(occupation_type_url)
            print(f"Number of {occupation}: {len(hrefs_for_famous_people_in_occupation_url)}")

            for href in hrefs_for_famous_people_in_occupation_url:
                name_of_famous_person = re.search("birth-chart/(.*)-horoscope", href).group(1)
                astro_chart_data_for_famous_person = self.get_astro_chart_data_for_famous_person(href)
                if astro_chart_data_for_famous_person is not None:
                    astro_chart_data_for_famous_person["name"] = name_of_famous_person
                    astro_chart_data_for_famous_person["occupation"] = occupation.split("famous-")[-1]
                astro_chart_data_for_people_by_occupation_type.append(astro_chart_data_for_famous_person)

            print(f"Time take to collect data: {round((time.time() - start_time) / 60, 2)} minutes")
            print("-" * 20)

        astro_chart_data_for_people_by_occupation_type = list(filter(None, astro_chart_data_for_people_by_occupation_type))
        astro_chart_data_df = pd.DataFrame(
            astro_chart_data_for_people_by_occupation_type,
            columns=list(astro_chart_data_for_people_by_occupation_type[0].keys())
        )

        return astro_chart_data_df

    def _get_hrefs_for_occupation_types(self, soup):
        all_search_by_options = soup.find(id='tabs_content_container')
        all_search_by_options_elements = all_search_by_options.find_all("div", class_='inv')

        hrefs_for_search_by_option = []
        for search_by_option_element in all_search_by_options_elements:
            search_by_option_classes = search_by_option_element.find_all(class_="tenky")

            for search_by_option_class in search_by_option_classes:
                search_by_option_class_href = search_by_option_class["href"]
                if "occupation" in search_by_option_class_href:
                    hrefs_for_search_by_option.append(search_by_option_class_href)

        return hrefs_for_search_by_option

    def _get_hrefs_for_famous_people_by_occupation_type(self, occupation_type_url):
        soup = get_beauiful_soup_object_from_base_url(occupation_type_url)
        number_of_famous_people_with_occupation_type = len(soup.find_all(class_="w260_p5"))

        if number_of_famous_people_with_occupation_type >= 200:
            all_pages_for_occupation_type = soup.find_all("a", href=re.compile("filter_occupation"))
            hrefs_for_all_pages = [page_class["href"] for page_class in all_pages_for_occupation_type]

            all_hrefs_for_famous_people_with_occupation_type = []
            for href in hrefs_for_all_pages:
                href_soup = get_beauiful_soup_object_from_base_url(href)
                hrefs_for_famous_people = self._get_hrefs_from_soup(href_soup)

                all_hrefs_for_famous_people_with_occupation_type.extend(hrefs_for_famous_people)
        else:
            all_hrefs_for_famous_people_with_occupation_type = self._get_hrefs_from_soup(soup)

        return all_hrefs_for_famous_people_with_occupation_type

    def _get_hrefs_from_soup(self, href_soup):
        famous_people_with_occupation_type = href_soup.find_all(class_="w260_p5")
        hrefs_for_famous_poeple = [
            famous_person.a["href"] for famous_person in famous_people_with_occupation_type
        ]

        return hrefs_for_famous_poeple

    def get_astro_chart_data_for_famous_person(self, href):
        soup = get_beauiful_soup_object_from_base_url(href)
        tags = soup.find_all("em")
        astro_chart_raw_data = [tag.text for tag in tags]

        try:
            astro_chart_data_for_famous_person = {
                "Birth time - local": astro_chart_raw_data[0],
                "Birth time - GMT": astro_chart_raw_data[1],
                "Birth longitude": astro_chart_raw_data[2],
                "Birth latitude": astro_chart_raw_data[3]
            }

        except IndexError:
            print(f"Data not found for {re.search('birth-chart/(.*)-horoscope', href).group(1)}")
            return None


        return astro_chart_data_for_famous_person


if __name__ == "__main__":
    base_url = "https://famouspeople.astro-seek.com/"
    occupations_not_considered = ["actor", "director"]

    astro_chart_loader = AstroSeekWebScraper(base_url)
    astro_chart_data_df = astro_chart_loader.load_raw_celebrity_astro_seek_data(occupations_not_considered)

    astro_chart_data_df.to_csv("raw_astro_seek_chart_data.csv", index=False)
    print(astro_chart_data_df.head())
