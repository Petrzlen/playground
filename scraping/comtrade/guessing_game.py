import json
import random

from utils import format_money


class Partner:
    def __init__(self, country, trade_value):
        self.country = country
        self.trade_value = trade_value


class ProductData:
    def __init__(self, product_code, product_name, direction):
        self.product_code = product_code
        self.product_name = product_name
        self.direction = direction
        self.partners = []
        self.total_trade_value = 0

    def add(self, data_row):
        partner = Partner(
            country=data_row["rtTitle"],
            trade_value=data_row["TradeValue"],
        )
        self.partners.append(partner)
        self.total_trade_value += partner.trade_value

    def is_good_game(self):
        return len(self.partners) > 5 and self.total_trade_value > 100000

    def run_game(self):
        assert self.is_good_game()
        self.partners.sort(key=lambda partner: -partner.trade_value)

        print(f"What is the top {self.direction} of {self.product_name} ({self.product_code})?")
        c = len(self.partners)
        # Pick randoms from all around the distribution and shuffle them.
        answer_indexes = [
            0,
            2*c//5,
            3*c//5,
            4*c//5,
        ]
        random.shuffle(answer_indexes)

        # Print the picking table.
        for i, partner_i in enumerate(answer_indexes):
            p = self.partners[partner_i]
            print(f"  {i+1}.) {p.country}")
        print(f"Hint: there are {c} with total trade value of {format_money(self.total_trade_value)}")

        # Evaluate the input
        answer = input()

        # Print the values in the end.
        partner_indexes = list(range(min(10, c)))
        partner_indexes.extend(answer_indexes)
        partner_indexes = list(set(partner_indexes))  # make them unique
        for partner_i in partner_indexes:
            p = self.partners[partner_i]
            was_an_answer = partner_i in answer_indexes
            extra = " (*)" if was_an_answer else ""
            print(f"{str(partner_i+1): <3}: {(p.country + extra)[:20]: <20}{format_money(p.trade_value)}")

        # TODO: Do here more.
        print(f"Your answer was: {answer}. Enter any string.")
        input()


# game[product][import][
with open("data/slovakia_2019.json", "r") as input_file:
    raw_data = json.load(input_file)

exports = {}
for row in raw_data:
    direction = row["rgDesc"]
    if direction == "Export":
        product_code = row["cmdCode"]
        product_name = row["cmdDescE"]
        if product_code not in exports:
            exports[product_code] = ProductData(product_code, product_name, direction)
        exports[product_code].add(row)

game_keys = list(exports.keys())
random.shuffle(game_keys)
for gk in game_keys:
    product_data = exports[gk]
    if not product_data.is_good_game():
        continue
    product_data.run_game()

# TODO: Result processing
#     {
#       "rgDesc": "Import",
#       "rtCode": 842,
#       "rtTitle": "USA",
#       "rt3ISO": "USA",
#       "cmdCode": "TOTAL",
#       "cmdDescE": "All Commodities",
#       "TradeValue": 2567492197103,
#     },