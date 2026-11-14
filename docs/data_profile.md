# Raw Data Profile

Generated 2026-11-14 20:33 by `etl/explore.py` on `data\downloads\amazon_reviews_2023` (full data).

## Volume per category

| category | reviews | users | products |
|---|---|---|---|
| All_Beauty | 701,528 | 631,986 | 112,565 |
| Appliances | 2,128,605 | 1,755,732 | 94,319 |

## Date range

| category | first_review | last_review |
|---|---|---|
| All_Beauty | 2000-11-01 | 2023-09-09 |
| Appliances | 2000-10-23 | 2023-09-12 |

## Reviews per year

| year | category | reviews |
|---|---|---|
| 2000 | All_Beauty | 1 |
| 2000 | Appliances | 1 |
| 2001 | All_Beauty | 12 |
| 2002 | All_Beauty | 24 |
| 2002 | Appliances | 1 |
| 2003 | All_Beauty | 56 |
| 2003 | Appliances | 8 |
| 2004 | All_Beauty | 134 |
| 2004 | Appliances | 16 |
| 2005 | All_Beauty | 267 |
| 2005 | Appliances | 80 |
| 2006 | All_Beauty | 418 |
| 2006 | Appliances | 179 |
| 2007 | All_Beauty | 1,163 |
| 2007 | Appliances | 624 |
| 2008 | All_Beauty | 1,268 |
| 2008 | Appliances | 883 |
| 2009 | All_Beauty | 1,207 |
| 2009 | Appliances | 1,537 |
| 2010 | All_Beauty | 1,585 |
| 2010 | Appliances | 3,535 |
| 2011 | All_Beauty | 1,876 |
| 2011 | Appliances | 7,625 |
| 2012 | All_Beauty | 2,797 |
| 2012 | Appliances | 15,196 |
| 2013 | All_Beauty | 7,952 |
| 2013 | Appliances | 43,602 |
| 2014 | All_Beauty | 16,251 |
| 2014 | Appliances | 77,233 |
| 2015 | All_Beauty | 36,246 |
| 2015 | Appliances | 122,765 |
| 2016 | All_Beauty | 62,701 |
| 2016 | Appliances | 153,847 |
| 2017 | All_Beauty | 68,060 |
| 2017 | Appliances | 169,839 |
| 2018 | All_Beauty | 72,697 |
| 2018 | Appliances | 189,498 |
| 2019 | All_Beauty | 99,060 |
| 2019 | Appliances | 260,889 |
| 2020 | All_Beauty | 126,758 |
| 2020 | Appliances | 311,190 |
| 2021 | All_Beauty | 124,940 |
| 2021 | Appliances | 345,219 |
| 2022 | All_Beauty | 61,609 |
| 2022 | Appliances | 299,440 |
| 2023 | All_Beauty | 14,446 |
| 2023 | Appliances | 125,398 |

## Rating distribution

| rating | reviews | pct |
|---|---|---|
| 1.00 | 352,533 | 12.46 |
| 2.00 | 122,698 | 4.34 |
| 3.00 | 160,354 | 5.67 |
| 4.00 | 287,597 | 10.16 |
| 5.00 | 1,906,951 | 67.38 |

## Data quality red flags (Day 2 rules come from here)

| null_user_id | null_parent_asin | bad_rating | null_timestamp | future_dates | empty_text | negative_votes |
|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 | 2,785 | 0 |

## Exact duplicates (same user + product + timestamp)

| duplicate_groups | extra_rows |
|---|---|
| 25,282 | 29,933 |

## Verified purchase share

| category | verified_pct | avg_rating_verified | avg_rating_unverified |
|---|---|---|---|
| All_Beauty | 90.51 | 3.95 | 4.08 |
| Appliances | 95.84 | 4.25 | 3.53 |

## Helpful votes

| pct_zero_votes | p50 | p90 | p99 | max |
|---|---|---|---|---|
| 78.94 | 0.00 | 1.00 | 15.00 | 5,704 |

## Review text length (characters)

| p50 | p90 | p99 | max |
|---|---|---|---|
| 92.00 | 387.00 | 1,230.00 | 30,004 |

## Most active reviewers (possible bots)

| user_id | reviews | avg_rating |
|---|---|---|
| AG73BVBKUOH22USSFJA5ZWL7AKXA | 177 | 4.51 |
| AEZP6Z2C5AVQDZAJECQYZWQRNG3Q | 149 | 4.15 |
| AEMP3A7IKW37CMWFXNKXWW6HGJHA_1 | 115 | 3.97 |
| AHJGIPM2BSL2PQIP2223Y2WVVAPQ | 111 | 4.38 |
| AHDVSLWHSORYGG3S5QZMVDFNOXUQ | 108 | 4.67 |

## Orphan reviews (product missing from product data)

| category | orphan_reviews | pct |
|---|---|---|

## Products: duplicate product rows

| duplicate_products |
|---|
| 0 |

## Products: field coverage

| category | products | has_price_pct | has_store_pct | has_brand_pct |
|---|---|---|---|---|
| All_Beauty | 112,590 | 15.70 | 89.90 | 64.00 |
| Appliances | 94,327 | 49.50 | 99.00 | 42.00 |

## Products: price values that aren't numbers

| price | products |
|---|---|

## Products: price distribution

| category | min | p25 | p50 | p75 | p99 | max |
|---|---|---|---|---|---|---|
| All_Beauty | 0.01 | 9.99 | 16.99 | 29.90 | 187.48 | 2,548.98 |
| Appliances | 0.01 | 14.99 | 26.99 | 58.13 | 1,282.88 | 21,095.62 |

## Decisions for Day 2

Fill this in after reading the tables above:

- Duplicates: 
- Orphan reviews: 
- Price parsing: 
- Brand source (details.Brand vs store): 
- Other: 
