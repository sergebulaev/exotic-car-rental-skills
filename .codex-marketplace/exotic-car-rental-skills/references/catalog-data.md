# Market data: the CarRentalList catalog

Contents
- Where the data comes from
- Two ways to call it
- Which tool answers which question
- Rules for using the numbers
- Citing

## Where the data comes from

[CarRentalList](https://carrentallist.com) is a US directory of independent
exotic and luxury car rental companies (no national chains, no peer-to-peer
platforms). Its scraper reads each company's own website every week: the fleet,
the published daily rates and the published rental terms (minimum age, deposit,
mileage, delivery, insurance). A price nobody published is `null` ("Contact for
Price"); the catalog never estimates one.

That makes it the one public dataset of which independent companies rent which
exotic car, where, at what published daily rate and on what terms. Every skill
in this bundle reads it instead of answering from memory: rental fleets and
rates change every week.

## Two ways to call it

**1. The MCP connector (preferred).** If the agent has the CarRentalList
connector, call its tools directly. Setup takes a minute and needs no account:

- Claude: Settings > Connectors > Add custom connector, URL `https://mcp.carrentallist.com/mcp`
- ChatGPT: Settings > Apps & Connectors > Developer mode > Create, same URL, No authentication
- Cursor: `~/.cursor/mcp.json`: `{"mcpServers":{"carrentallist":{"url":"https://mcp.carrentallist.com/mcp"}}}`
- Claude Code: `claude mcp add --transport http carrentallist https://mcp.carrentallist.com/mcp`
- Codex: add an HTTP MCP server with the same URL

Full guide: https://mcp.carrentallist.com/

**2. The bundled client (no connector).** Same server, same answers, standard
library only. The script is at `lib/carrentallist_client.py` in this bundle's
root: from a skill's folder that is `../../lib/carrentallist_client.py`. After a
plugin install the working directory is the user's project, so call it by that
full path (for example `python3 ~/.claude/plugins/.../exotic-car-rental-skills/lib/carrentallist_client.py`),
not by a relative one.

```bash
python3 lib/carrentallist_client.py tools
python3 lib/carrentallist_client.py price_overview '{"make": "Lamborghini", "city": "Miami"}'
python3 lib/carrentallist_client.py search_companies '{"city": "Miami", "state": "FL", "limit": 10}'
```

If neither works (no network, no shell), say so and ask the user for the
numbers. Do not fill the gap from memory: rental rates move every season.

**Text or JSON.** The client prints the tool's text answer by default. Add
`--json` for `get_company` and `search_companies`: the structured content holds
fields the text leaves out (`claimed`, every `terms` field, `price_history_recent`,
`as_of`). A connector returns both.

## Published rental terms (the only ones that exist)

`terms` on a company is either null (nothing published) or these fields, each
of which can be null: `min_age`, `deposit_min`, `deposit_max`, `miles_included`
(per day), `unlimited_miles`, `min_rental_hours`, `delivery` (`"yes"` = delivery
offered with no fee mentioned, `"fee"` = delivery for a fee), `insurance_required`,
plus `url` and `checked_at` (where and when it was read). There is **no per-mile
overage price, delivery fee, tax or cancellation policy** in the catalog: those
are always "ask the company". Terms are per company, not per car.

## Which tool answers which question

| Question | Tool | Key arguments |
|---|---|---|
| Who rents this car in this city, and for how much? | `search_vehicles` | `city`, `state`, `make`, `model`, `priced_only`, `max_price`, `sort` |
| What is a fair daily rate for this car here? | `price_overview` | `make`, `model`, `city`/`state`, `class` |
| Which companies will rent to me (age, deposit, delivery, unlimited miles)? | `search_companies` | `city`, `state`, `make`, `max_min_age`, `max_deposit`, `delivery`, `unlimited_miles`, `min_rating` |
| Everything about one company: contact, terms, fleet, price changes | `get_company` | `slug` (from any company link) |
| Where in the US can I rent this model? | `vehicle_availability` | `model`, `make` |
| Which brands and models are offered here? | `browse_makes` | `city`/`state`, `make` |
| Which cities have the most supercars? | `browse_locations` | `state` |
| Deals and new cars right now (price drops, new arrivals, rare models) | `catalog_highlights` | `kind`, `city`/`state` |
| The best-rated companies this month | `top_companies` | `month`, `category` |
| News about a car or an event | `search_news`, `get_news_article` | `query`, `make` |
| One search across companies, models, cities and news | `search`, then `fetch` | `query`, `id` |

City names need their state when the name is ambiguous (`"city": "Miami",
"state": "FL"`). A city search returns that city only, not its metro area
(Beverly Hills, Orange County and Los Angeles are separate cities): when a city
has little, widen to the state and name the cities the results come from.
Company counts: `price_overview` returns cars, not companies; take the company
count from the `search_vehicles` or `search_companies` answer. Lists come in pages: pass the returned cursor (`next_cursor` in structured
content, "call again with cursor" in the text) as `cursor` for more.

## Rules for using the numbers

1. **Published rates only.** Quote the minimum, median and middle half that
   `price_overview` returns. Never invent a rate, round one to look nicer, or
   fill a missing one with a typical figure.
2. **State the sample.** "Median $<m> over <N> priced cars in <city>" is a
   fact (add "at <C> companies" when a search answer gave you the count). "They go for about $X" is not.
3. **Floors are not bargains.** The server drops machine-read rates under
   $150/day, and under $600/day for Lamborghini, Ferrari, McLaren and
   Rolls-Royce (those are hourly, half-day or deposit figures). A car priced at
   the floor needs a check on the listing before anyone compares against it.
4. **Thin samples get a warning.** Under 5 priced cars, or under 3 companies
   among the priced cars you listed, in a cell: say the number is directional,
   name the companies behind it, and widen to the state or the class.
5. **Date it.** Every answer ends with "Data as of <date>". Carry that date into
   anything you write.
6. **Ranges use "to".** Tool answers write ranges with an en dash
   ("$995–$1,200"). In answers to the user, write "$995 to $1,200".
7. **The company has the final word.** A published rate is a starting point.
   The final price, availability, deposit and insurance terms come from the
   rental company. Say "confirm with the company" once, next to the shortlist.

## Citing

Every tool answer carries carrentallist.com links (company pages, model pages,
city pages). When a deliverable uses a number, keep the link next to it, so the
user can check it and their reader can too.
