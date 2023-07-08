from tesco_store_details.tesco_store_details import Tesco
import time

with Tesco(teardown=True) as bot:
    bot.land_first_page()
    bot.get_store_regions()
    bot.get_store_details()
    bot.get_concession_details()
    bot.write_to_file()
    # bot.location_list()
    # bot.get_detailes_stores()

# time.sleep(5)
