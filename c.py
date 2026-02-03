# from curl_cffi import requests
#
# url = "https://resume.service.tealhq.com/job_posts?page=5&per_page=20"
#
# payload = {}
# headers = {
#   'accept': 'application/json, text/plain, */*',
#   'accept-language': 'en-US,en;q=0.9',
#   'authorization': 'Bearer eyJhbGciOiJSUzI1NiJ9.eyJ0eXBlIjoiYXV0aGVkIHVzZXIiLCJsaW5rZWRpbl9pZCI6bnVsbCwiZW1haWwiOiJtemVlc2hhbm16ZWVAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWRfYXQiOm51bGwsInJvbGUiOiJ1c2VyIiwiZmlyc3RfbmFtZSI6Ik1PSEFNTUFEIiwibGFzdF9uYW1lIjoiWkVFU0hBTiIsImFjdGl2ZV9zdWJzY3JpcHRpb25zIjpbXSwidXVpZCI6ImVhNzM5OTZkLWEzZWQtNDdlMC04ZTBmLTg2M2RlMmU3ZDk2MCIsImp3dF9jcmVhdGVkX2F0IjoiMjAyNi0wMS0zMSIsImlhdCI6MTc2OTg4MzUyNCwiYXJjaGl2ZWRfYXQiOm51bGwsImV4cCI6MTc3NzU3MzEyNCwidXNlcl9jcmVhdGVkX2F0IjoiMjAyNC0wMS0xOSAwNjoyMzoyMCBVVEMiLCJjb2hvcnRfaWQiOiIxMWVkODQzYy02Njg1LTQ3M2MtOWNmNS00ZDgyNDYxZGQ3M2YiLCJ0YXJnZXRfdGl0bGUiOiJweXRob24gc29mdHdhcmUgZW5naW5lZXIgIiwiZmVhdHVyZV9zbmFwc2hvdCI6eyJsaW1pdC1qb2ItdHJhY2tlci1lbWFpbC10ZW1wbGF0ZXMiOnRydWUsImxpbWl0LWpvYi1tYXRjaGluZy1rZXl3b3JkcyI6dHJ1ZSwibGltaXQtam9iLXRyYWNrZXIta2V5d29yZHMiOnRydWUsImxpbWl0LXJlc3VtZS1hbmFseXNpcy1yZWNvbW1lbmRhdGlvbnMiOnRydWUsInNob3ctYWRzIjp0cnVlLCJsaW1pdC1hY2hpZXZlbWVudC1nZW5lcmF0aW9ucyI6dHJ1ZSwibGltaXQtYmx1cmItZ2VuZXJhdGlvbnMiOnRydWUsImxpbWl0LWNvdmVyLWxldHRlci1nZW5lcmF0aW9ucyI6dHJ1ZSwibGltaXQtYWNoaWV2ZW1lbnQtYW5hbHlzZXMiOnRydWV9LCJmZWF0dXJlX3NuYXBzaG90X3YyIjp7ImxpbWl0LWpvYi10cmFja2VyLWVtYWlsLXRlbXBsYXRlcyI6eyJpc19hY3RpdmUiOnRydWUsIm1ldGEiOnt9fSwibGltaXQtam9iLW1hdGNoaW5nLWtleXdvcmRzIjp7ImlzX2FjdGl2ZSI6dHJ1ZSwibWV0YSI6e319LCJsaW1pdC1qb2ItdHJhY2tlci1rZXl3b3JkcyI6eyJpc19hY3RpdmUiOnRydWUsIm1ldGEiOnt9fSwibGltaXQtcmVzdW1lLWFuYWx5c2lzLXJlY29tbWVuZGF0aW9ucyI6eyJpc19hY3RpdmUiOnRydWUsIm1ldGEiOnt9fSwic2hvdy1hZHMiOnsiaXNfYWN0aXZlIjp0cnVlLCJtZXRhIjp7fX0sImxpbWl0LWFjaGlldmVtZW50LWdlbmVyYXRpb25zIjp7ImlzX2FjdGl2ZSI6dHJ1ZSwibWV0YSI6eyJtYXgiOjMwfX0sImxpbWl0LWJsdXJiLWdlbmVyYXRpb25zIjp7ImlzX2FjdGl2ZSI6dHJ1ZSwibWV0YSI6e319LCJsaW1pdC1jb3Zlci1sZXR0ZXItZ2VuZXJhdGlvbnMiOnsiaXNfYWN0aXZlIjp0cnVlLCJtZXRhIjp7fX0sImxpbWl0LWFjaGlldmVtZW50LWFuYWx5c2VzIjp7ImlzX2FjdGl2ZSI6dHJ1ZSwibWV0YSI6eyJtYXgiOjV9fX0sImludGVyY29tX2htYWNfY29kZSI6ImVkZmE2NmQ5MjE3NzM0ZGFkZThjNjFlMzc1NjY0OGVjNTZhZjQxMDA3Yjk1MmJkOTFiMzg0NWY0MDE4OWY1NTEifQ.r4bCsIIcelIrltAz5UVkvR6jf63Gjw0rChq76QKMSxA8o-sHuRT7YPBV8dm8RQq4VS4GNc5eyn-vqhu2bZA2Bs4m-KyOf0Ij06tkEeKPqgcta2HN8XVDZ1pET63o9ZFUXy4D40KkFQDDTu2tQlTt_rarlFAYJCcpGZ2P-vS1FsmbiQ8knCi9su1_uc1UH9ZKnNwJLrgDnR1jp1QpBIhIzV7jw-bo3xPM3hqW6aYAOmKzHYWEdCi-Tf5DUyz42SK-qNQb8VLqfnLS9C7lv6qdJKCs2MdfOydC1rPyo7TmefC2a7vrNaVkn1eje1mQhxp0eEYQsmXEhNWGwdRclKhDZg',
#   'origin': 'https://app.tealhq.com',
#   'priority': 'u=1, i',
#   'referer': 'https://app.tealhq.com/',
#   'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
#   'sec-ch-ua-mobile': '?0',
#   'sec-ch-ua-platform': '"macOS"',
#   'sec-fetch-dest': 'empty',
#   'sec-fetch-mode': 'cors',
#   'sec-fetch-site': 'same-site',
#   'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
#   'Cookie': '__cf_bm=IxULseTn_FvW9lktxfhmdFUyaqM1Kh1NYUE9TQmNdUk-1769889368.6087272-1.0.1.1-iFpy1NtYOeSeKygMm1IzOJSmGthI..ZiGQcq9OlRg.e6NdbWQRJQxyibZvtxppu4CX84AWF9v.cZPPuholguoHNRiEDkz9vhV_JyLBLM3m21HPrSeBQuAaEaGD_peP0m'
# }
#
# # response = requests.request("GET", url, headers=headers, data=payload)
# response = requests.get(url=url, headers=headers, impersonate="chrome")
# print(response.text)
#
#
# from curl_cffi import requests
# job_post_id = "7ea1a0547c5753df3f479b83bd7da3e576638"
# url = f"https://resume.service.tealhq.com/job_posts/{job_post_id}"
#
# headers = {
#     "accept": "application/json, text/plain, */*",
#     "accept-language": "en-US,en;q=0.9",
#     "authorization": "Bearer eyJhbGciOiJSUzI1NiJ9.eyJ0eXBlIjoiYXV0aGVkIHVzZXIiLCJsaW5rZWRpbl9pZCI6bnVsbCwiZW1haWwiOiJtemVlc2hhbm16ZWVAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWRfYXQiOm51bGwsInJvbGUiOiJ1c2VyIiwiZmlyc3RfbmFtZSI6Ik1PSEFNTUFEIiwibGFzdF9uYW1lIjoiWkVFU0hBTiIsImFjdGl2ZV9zdWJzY3JpcHRpb25zIjpbXSwidXVpZCI6ImVhNzM5OTZkLWEzZWQtNDdlMC04ZTBmLTg2M2RlMmU3ZDk2MCIsImp3dF9jcmVhdGVkX2F0IjoiMjAyNi0wMS0zMSIsImlhdCI6MTc2OTg4MzUyNCwiYXJjaGl2ZWRfYXQiOm51bGwsImV4cCI6MTc3NzU3MzEyNCwidXNlcl9jcmVhdGVkX2F0IjoiMjAyNC0wMS0xOSAwNjoyMzoyMCBVVEMiLCJjb2hvcnRfaWQiOiIxMWVkODQzYy02Njg1LTQ3M2MtOWNmNS00ZDgyNDYxZGQ3M2YiLCJ0YXJnZXRfdGl0bGUiOiJweXRob24gc29mdHdhcmUgZW5naW5lZXIgIiwiZmVhdHVyZV9zbmFwc2hvdCI6eyJsaW1pdC1qb2ItdHJhY2tlci1lbWFpbC10ZW1wbGF0ZXMiOnRydWUsImxpbWl0LWpvYi1tYXRjaGluZy1rZXl3b3JkcyI6dHJ1ZSwibGltaXQtam9iLXRyYWNrZXIta2V5d29yZHMiOnRydWUsImxpbWl0LXJlc3VtZS1hbmFseXNpcy1yZWNvbW1lbmRhdGlvbnMiOnRydWUsInNob3ctYWRzIjp0cnVlLCJsaW1pdC1hY2hpZXZlbWVudC1nZW5lcmF0aW9ucyI6dHJ1ZSwibGltaXQtYmx1cmItZ2VuZXJhdGlvbnMiOnRydWUsImxpbWl0LWNvdmVyLWxldHRlci1nZW5lcmF0aW9ucyI6dHJ1ZSwibGltaXQtYWNoaWV2ZW1lbnQtYW5hbHlzZXMiOnRydWV9LCJmZWF0dXJlX3NuYXBzaG90X3YyIjp7ImxpbWl0LWpvYi10cmFja2VyLWVtYWlsLXRlbXBsYXRlcyI6eyJpc19hY3RpdmUiOnRydWUsIm1ldGEiOnt9fSwibGltaXQtam9iLW1hdGNoaW5nLWtleXdvcmRzIjp7ImlzX2FjdGl2ZSI6dHJ1ZSwibWV0YSI6e319LCJsaW1pdC1qb2ItdHJhY2tlci1rZXl3b3JkcyI6eyJpc19hY3RpdmUiOnRydWUsIm1ldGEiOnt9fSwibGltaXQtcmVzdW1lLWFuYWx5c2lzLXJlY29tbWVuZGF0aW9ucyI6eyJpc19hY3RpdmUiOnRydWUsIm1ldGEiOnt9fSwic2hvdy1hZHMiOnsiaXNfYWN0aXZlIjp0cnVlLCJtZXRhIjp7fX0sImxpbWl0LWFjaGlldmVtZW50LWdlbmVyYXRpb25zIjp7ImlzX2FjdGl2ZSI6dHJ1ZSwibWV0YSI6eyJtYXgiOjMwfX0sImxpbWl0LWJsdXJiLWdlbmVyYXRpb25zIjp7ImlzX2FjdGl2ZSI6dHJ1ZSwibWV0YSI6e319LCJsaW1pdC1jb3Zlci1sZXR0ZXItZ2VuZXJhdGlvbnMiOnsiaXNfYWN0aXZlIjp0cnVlLCJtZXRhIjp7fX0sImxpbWl0LWFjaGlldmVtZW50LWFuYWx5c2VzIjp7ImlzX2FjdGl2ZSI6dHJ1ZSwibWV0YSI6eyJtYXgiOjV9fX0sImludGVyY29tX2htYWNfY29kZSI6ImVkZmE2NmQ5MjE3NzM0ZGFkZThjNjFlMzc1NjY0OGVjNTZhZjQxMDA3Yjk1MmJkOTFiMzg0NWY0MDE4OWY1NTEifQ.r4bCsIIcelIrltAz5UVkvR6jf63Gjw0rChq76QKMSxA8o-sHuRT7YPBV8dm8RQq4VS4GNc5eyn-vqhu2bZA2Bs4m-KyOf0Ij06tkEeKPqgcta2HN8XVDZ1pET63o9ZFUXy4D40KkFQDDTu2tQlTt_rarlFAYJCcpGZ2P-vS1FsmbiQ8knCi9su1_uc1UH9ZKnNwJLrgDnR1jp1QpBIhIzV7jw-bo3xPM3hqW6aYAOmKzHYWEdCi-Tf5DUyz42SK-qNQb8VLqfnLS9C7lv6qdJKCs2MdfOydC1rPyo7TmefC2a7vrNaVkn1eje1mQhxp0eEYQsmXEhNWGwdRclKhDZg",
#     "origin": "https://app.tealhq.com",
#     "referer": "https://app.tealhq.com/",
#     "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
#     "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
#     "sec-ch-ua-mobile": "?0",
#     "sec-ch-ua-platform": '"macOS"',
#     "sec-fetch-dest": "empty",
#     "sec-fetch-mode": "cors",
#     "sec-fetch-site": "same-site",
#     "cookie": "__cf_bm=gASM3s0QhVhmoPjJ88wko3GbPV50grBv6nHOwTu2hbQ-1769890169.1641576-1.0.1.1-y9LpG_N32DGqVj6yUqWZLeCpXuGKxhs1Hf2hOKsHza7l4mJuW9L.bUkFLTeM30Y1OIiulNTKtOyXXtWbnOg14fBHbFI1aWcxPf9LWGROluFCyYG.I_9676Eop3VWDqdT",
# }
#
# response = requests.get(
#     url,
#     headers=headers,
#     impersonate="chrome"
# )
#
# print(response.text)
# print(response.status_code)

#
# # indeed apis
# from curl_cffi import requests
#
# response = requests.get(
#     url="https://pk.indeed.com/jobs",
#     params={
#         "q": "python developer",
#         "l": "",
#         "from": "searchOnDesktopSerp,whatautocomplete,whatautocompleteSourceStandard",
#     },
#     headers={
#         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
#         "accept-language": "en-US,en;q=0.9",
#         "referer": "https://pk.indeed.com/jobs?q=remote&l=&from=searchOnHP%2CsearchSuggestions%2CwhatautocompleteSourceStandard",
#         "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
#         "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
#         "sec-ch-ua-mobile": "?0",
#         "sec-ch-ua-platform": '"macOS"',
#         "upgrade-insecure-requests": "1",
#     },
#     cookies={
#         "CTK": "1jbna6lnhit6n80b",
#         "LC": "co=PK",
#         "CO": "PK",
#         "LOCALE": "en_PK",
#         "cf_clearance": "2PgQTETiA432xKnj87IIef6JkEywJtgDY5JZSfuOVjg-1769949832-1.2.1.1-lpTjtgZKnwD96GaL9Z8zCvqJyGKbn02hgVXAqaIczEliY.Om2fDknQ630nvAefBuz0bIIGCatsq_Czww7mAqvvFrl9RYvqGGo5zRLy.EGujXBBg9gKhA.tHXMvw0rALAq91xLx7pYdKCEi72bd250N8puzW8JxkrqCSgKwcGIxYGYqTp2FTobTDtXKKNs.58YvXqsFIlPPuHRotX334kdamhesHhc2.FGI3qdjfslnE",
#         "__cf_bm": "V.4h70j6GsMjQMIu_wu0uTyppIYRg9bPNJDkrbvrLBM-1769949830-1.0.1.1-kh45g8HtEYr2Q6OF1PzJpy6CuNx12_sofqAEvqes_JAjg3UZsriA5WU0fiUYl0wlN6_niHt2I7RsKfnKCo9UATmiLgg_GvSI1rX6uTCoLUc",
#     },
#     impersonate="from curl_cffi import requests
# import json
#
# payload = {
#     "keywords": "python ",
#     "location": "",
#     "country": "PAK",
#     "radius": 0,
#     "minSalary": 350000,
#     "maxSalary": -1,
#     "initialSearchId": 0,
#     "refinedSearchId": 0,
#     "lastExecutedSearch": None,
#     "searchFiltering": 0,
#     "featuredJobs": "",
#     "origin": 1,
#     "savedSearchId": None,
#     "startIndex": 0,
#     "limit": 25,
#     "filters": {}
# }
#
# headers = {
#     "accept": "application/json, text/plain, */*",
#     "accept-language": "en-US,en;q=0.9",
#     "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3Njk5NzY4MzYsImV4cCI6MTc3MDA2MzIzNiwicm9sZXMiOlsiSVNfQVVUSEVOVElDQVRFRF9SRU1FTUJFUkVEIl0sInVzZXJuYW1lIjoieWlub3hpbjU1NkBneHV6aS5jb20iLCJpZCI6NTgyNTYyMTIsIm1kNVVzZXIiOiJjMmFiODA5NjhlZWE3MjhlYjljZjIyNDRjYzM3MjE5OSIsInVjIjoyNiwibG9jYWxpemF0aW9uIjoie1wibG9jYWxlXCI6XCJlbl9QS1wiLFwid29ybGRSZWdpb25cIjpcIlBha2lzdGFuXCJ9IiwiaXNfcHJlbWl1bSI6ZmFsc2V9.L26O-xFHQF15UgHPxOQnZlGGpYZfUCfLaM0vhXj3brOaZSIH8a3xygAZb6JdTLaIgFTSF8zmzupZeV8QM7OJg15QZbm5JAF-J68Kbmtkoroz39iXZ33Jpm5RcyMFEwOJbUnuhOvonUfgKpGLdwYeTLCHjESrV3fHcH7AgHT86dCXuFiGAdGCY_ivlvRIN42ytIjURa9DS5z_0x8L2HakGlmAO5WbLhxcJMapzk8x81g04NF-LWQD_W9q4UKOK98z7A3g4Gd0FGUB1okwDgRyCr9bxTq-ZEUgcep6x4bUaa1tKVYTCUutowOcKaD4iox4kQg-BeFbV_HUB7U-zjfaq6QKilJbqXvKPzfh67w63wh115LdqK6CTIdZEBoUNg_PutjnH_OxR8aIl68LHj_lxOsPmXK-mOjjfxu2VLJz-Dgr4FG8eFxjJn-zHbZdExxGMQNfzwx8-oc-bAbl8KRKoeeABYGeHiwA4E31gs34jWjahiTIQIXRLH52pmT21x45LqhZBmheDqwmrMXY9LjOSKdiUA3SdtvYJl5LWl7kSvQZL-JFpGoSPNNNUXNkgHjEFmQJnxi6pNZyX5D7ApDbVbcue-gfL2lKn3JMrG8Q7Q7QOxwZa0ABVks5gLfcTiYhMxJ5cdrgWSfVSySedPjEqZq-7YaQBLG2nL_MMhL6-Fg",
#     "baggage": "sentry-environment=production,sentry-release=vue-shop%402.2.7,sentry-public_key=8119fab78b48d4d0b570b9a4268fb473,sentry-trace_id=78e8afd7fc5e41dca8bc6c479075b915,sentry-replay_id=cba9a516ea89441096de20a387315637",
#     "cf-ipcountry": "PK",
#     "content-type": "application/json",
#     "origin": "https://www.jobleads.com",
#     "priority": "u=1, i",
#     "referer": "https://www.jobleads.com/search/jobs?keywords=python+&location=&location_country=PAK&minSalary=350000&maxSalary=-1",
#     "sec-ch-ua": "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
#     "sec-ch-ua-mobile": "?0",
#     "sec-ch-ua-platform": "\"macOS\"",
#     "sec-fetch-dest": "empty",
#     "sec-fetch-mode": "cors",
#     "sec-fetch-site": "same-origin",
#     "sentry-trace": "78e8afd7fc5e41dca8bc6c479075b915-882feece29f958a3",
#     "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
#     "x-requested-with": "XMLHttpRequest",
# }
#
# cookies = {
#     "locale": "en_PK; cookie_version=1.1; optimizelySession=0; g_state={\"i_l\":0,\"i_ll\":1768844962769,\"i_b\":\"wliWJFnwYOb7WsoaziI4zhapIdDTiVAGJq9XJDNA49M\",\"i_e\":{\"enable_itp_optimization\":0}}; jlst=1f0ffaa5-4f50-6398-8660-0dd9927f615c; __cf_bm=wJLFNUJuqMtOu7ebrtihvVRLFxeifkvnFd9yL7qVVdY-1769976748-1.0.1.1-s9ihQpXjOcY21AwOD1xM_JZ0YTb2gqJcOEc08HMW4fkxlABv5P7pwds7ZxEQFvQKv9bxZac0Dm.e9zuVHGtzVC1oeuluQwpyEWJMwBqwJH8; prodsid=na1v0b7jhaoc0as5gr37c2nhse; oj=%7B%22t%22%3A%7B%22Source%22%3A%22linkedin-ads_PK-Evergreen-HH-FMJ_PK__%22%2C%22Campaign%22%3A%22PK-Evergreen-HH-FMJ%22%2C%22Medium%22%3A%22linkedin-ad%22%2C%22Content%22%3A%22PK-SIA-JobSeekersCareerChangers-HH-FMJ-NB_ncfh04-rebrand_value-of-headhunters_base-short%22%2C%22Term%22%3Anull%2C%22CreatedAt%22%3A%222026-02-01%2021%3A13%3A07%22%2C%22ClickId%22%3Anull%2C%22BingClickId%22%3Anull%2C%22FacebookClickId%22%3Anull%2C%22LinkedInClickId%22%3A%22cfeb58f7-91c3-42a0-ab89-439a4434715b%22%2C%22PartnerSubId%22%3A%22%22%7D%2C%22r%22%3A%22https%3A%5C%2F%5C%2Ftemp-mail.org%5C%2F%22%7D; jwt_hp=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3Njk5NzY4MzYsImV4cCI6MTc3MDA2MzIzNiwicm9sZXMiOlsiSVNfQVVUSEVOVElDQVRFRF9SRU1FTUJFUkVEIl0sInVzZXJuYW1lIjoieWlub3hpbjU1NkBneHV6aS5jb20iLCJpZCI6NTgyNTYyMTIsIm1kNVVzZXIiOiJjMmFiODA5NjhlZWE3MjhlYjljZjIyNDRjYzM3MjE5OSIsInVjIjoyNiwibG9jYWxpemF0aW9uIjoie1wibG9jYWxlXCI6XCJlbl9QS1wiLFwid29ybGRSZWdpb25cIjpcIlBha2lzdGFuXCJ9IiwiaXNfcHJlbWl1bSI6ZmFsc2V9; jwt_s=L26O-xFHQF15UgHPxOQnZlGGpYZfUCfLaM0vhXj3brOaZSIH8a3xygAZb6JdTLaIgFTSF8zmzupZeV8QM7OJg15QZbm5JAF-J68Kbmtkoroz39iXZ33Jpm5RcyMFEwOJbUnuhOvonUfgKpGLdwYeTLCHjESrV3fHcH7AgHT86dCXuFiGAdGCY_ivlvRIN42ytIjURa9DS5z_0x8L2HakGlmAO5WbLhxcJMapzk8x81g04NF-LWQD_W9q4UKOK98z7A3g4Gd0FGUB1okwDgRyCr9bxTq-ZEUgcep6x4bUaa1tKVYTCUutowOcKaD4iox4kQg-BeFbV_HUB7U-zjfaq6QKilJbqXvKPzfh67w63wh115LdqK6CTIdZEBoUNg_PutjnH_OxR8aIl68LHj_lxOsPmXK-mOjjfxu2VLJz-Dgr4FG8eFxjJn-zHbZdExxGMQNfzwx8-oc-bAbl8KRKoeeABYGeHiwA4E31gs34jWjahiTIQIXRLH52pmT21x45LqhZBmheDqwmrMXY9LjOSKdiUA3SdtvYJl5LWl7kSvQZL-JFpGoSPNNNUXNkgHjEFmQJnxi6pNZyX5D7ApDbVbcue-gfL2lKn3JMrG8Q7Q7QOxwZa0ABVks5gLfcTiYhMxJ5cdrgWSfVSySedPjEqZq-7YaQBLG2nL_MMhL6-Fg; ssr_i18n=en; user_i18n=en; __Host-csrf=e6118a37-0812-4ed6-8b81-ed883bc76e03"
# }
#
# resp = requests.post(
#     "https://www.jobleads.com/api/v2/search/v2",
#     headers=headers,
#     cookies=cookies,
#     json=payload,             # use json= instead of data= for proper JSON encoding
#     impersonate="chrome124"   # pick a close browser fingerprint (you can change this)
# )
#
# print(resp.status_code)
# print(resp.text)",
#     # http2=True,
# )
#
# print(response.text)
# print(response.status_code)


# jobleads
# from curl_cffi import requests
# import json
#
# payload = {
#     "keywords": "python ",
#     "location": "",
#     "country": "PAK",
#     "radius": 0,
#     "minSalary": 350000,
#     "maxSalary": -1,
#     "initialSearchId": 0,
#     "refinedSearchId": 0,
#     "lastExecutedSearch": None,
#     "searchFiltering": 0,
#     "featuredJobs": "",
#     "origin": 1,
#     "savedSearchId": None,
#     "startIndex": 0,
#     "limit": 25,
#     "filters": {}
#     # "filters": {"daysReleased": "31"," remote": "remote"}
# }
#
# headers = {
#     "accept": "application/json, text/plain, */*",
#     "accept-language": "en-US,en;q=0.9",
#     "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3Njk5NzY4MzYsImV4cCI6MTc3MDA2MzIzNiwicm9sZXMiOlsiSVNfQVVUSEVOVElDQVRFRF9SRU1FTUJFUkVEIl0sInVzZXJuYW1lIjoieWlub3hpbjU1NkBneHV6aS5jb20iLCJpZCI6NTgyNTYyMTIsIm1kNVVzZXIiOiJjMmFiODA5NjhlZWE3MjhlYjljZjIyNDRjYzM3MjE5OSIsInVjIjoyNiwibG9jYWxpemF0aW9uIjoie1wibG9jYWxlXCI6XCJlbl9QS1wiLFwid29ybGRSZWdpb25cIjpcIlBha2lzdGFuXCJ9IiwiaXNfcHJlbWl1bSI6ZmFsc2V9.L26O-xFHQF15UgHPxOQnZlGGpYZfUCfLaM0vhXj3brOaZSIH8a3xygAZb6JdTLaIgFTSF8zmzupZeV8QM7OJg15QZbm5JAF-J68Kbmtkoroz39iXZ33Jpm5RcyMFEwOJbUnuhOvonUfgKpGLdwYeTLCHjESrV3fHcH7AgHT86dCXuFiGAdGCY_ivlvRIN42ytIjURa9DS5z_0x8L2HakGlmAO5WbLhxcJMapzk8x81g04NF-LWQD_W9q4UKOK98z7A3g4Gd0FGUB1okwDgRyCr9bxTq-ZEUgcep6x4bUaa1tKVYTCUutowOcKaD4iox4kQg-BeFbV_HUB7U-zjfaq6QKilJbqXvKPzfh67w63wh115LdqK6CTIdZEBoUNg_PutjnH_OxR8aIl68LHj_lxOsPmXK-mOjjfxu2VLJz-Dgr4FG8eFxjJn-zHbZdExxGMQNfzwx8-oc-bAbl8KRKoeeABYGeHiwA4E31gs34jWjahiTIQIXRLH52pmT21x45LqhZBmheDqwmrMXY9LjOSKdiUA3SdtvYJl5LWl7kSvQZL-JFpGoSPNNNUXNkgHjEFmQJnxi6pNZyX5D7ApDbVbcue-gfL2lKn3JMrG8Q7Q7QOxwZa0ABVks5gLfcTiYhMxJ5cdrgWSfVSySedPjEqZq-7YaQBLG2nL_MMhL6-Fg",
#     "baggage": "sentry-environment=production,sentry-release=vue-shop%402.2.7,sentry-public_key=8119fab78b48d4d0b570b9a4268fb473,sentry-trace_id=78e8afd7fc5e41dca8bc6c479075b915,sentry-replay_id=cba9a516ea89441096de20a387315637",
#     "cf-ipcountry": "PK",
#     "content-type": "application/json",
#     "origin": "https://www.jobleads.com",
#     "priority": "u=1, i",
#     "referer": "https://www.jobleads.com/search/jobs?keywords=python+&location=&location_country=PAK&minSalary=350000&maxSalary=-1",
#     "sec-ch-ua": "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
#     "sec-ch-ua-mobile": "?0",
#     "sec-ch-ua-platform": "\"macOS\"",
#     "sec-fetch-dest": "empty",
#     "sec-fetch-mode": "cors",
#     "sec-fetch-site": "same-origin",
#     "sentry-trace": "78e8afd7fc5e41dca8bc6c479075b915-882feece29f958a3",
#     "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
#     "x-requested-with": "XMLHttpRequest",
# }
#
# cookies = {
#     "locale": "en_PK; cookie_version=1.1; optimizelySession=0; g_state={\"i_l\":0,\"i_ll\":1768844962769,\"i_b\":\"wliWJFnwYOb7WsoaziI4zhapIdDTiVAGJq9XJDNA49M\",\"i_e\":{\"enable_itp_optimization\":0}}; jlst=1f0ffaa5-4f50-6398-8660-0dd9927f615c; __cf_bm=wJLFNUJuqMtOu7ebrtihvVRLFxeifkvnFd9yL7qVVdY-1769976748-1.0.1.1-s9ihQpXjOcY21AwOD1xM_JZ0YTb2gqJcOEc08HMW4fkxlABv5P7pwds7ZxEQFvQKv9bxZac0Dm.e9zuVHGtzVC1oeuluQwpyEWJMwBqwJH8; prodsid=na1v0b7jhaoc0as5gr37c2nhse; oj=%7B%22t%22%3A%7B%22Source%22%3A%22linkedin-ads_PK-Evergreen-HH-FMJ_PK__%22%2C%22Campaign%22%3A%22PK-Evergreen-HH-FMJ%22%2C%22Medium%22%3A%22linkedin-ad%22%2C%22Content%22%3A%22PK-SIA-JobSeekersCareerChangers-HH-FMJ-NB_ncfh04-rebrand_value-of-headhunters_base-short%22%2C%22Term%22%3Anull%2C%22CreatedAt%22%3A%222026-02-01%2021%3A13%3A07%22%2C%22ClickId%22%3Anull%2C%22BingClickId%22%3Anull%2C%22FacebookClickId%22%3Anull%2C%22LinkedInClickId%22%3A%22cfeb58f7-91c3-42a0-ab89-439a4434715b%22%2C%22PartnerSubId%22%3A%22%22%7D%2C%22r%22%3A%22https%3A%5C%2F%5C%2Ftemp-mail.org%5C%2F%22%7D; jwt_hp=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3Njk5NzY4MzYsImV4cCI6MTc3MDA2MzIzNiwicm9sZXMiOlsiSVNfQVVUSEVOVElDQVRFRF9SRU1FTUJFUkVEIl0sInVzZXJuYW1lIjoieWlub3hpbjU1NkBneHV6aS5jb20iLCJpZCI6NTgyNTYyMTIsIm1kNVVzZXIiOiJjMmFiODA5NjhlZWE3MjhlYjljZjIyNDRjYzM3MjE5OSIsInVjIjoyNiwibG9jYWxpemF0aW9uIjoie1wibG9jYWxlXCI6XCJlbl9QS1wiLFwid29ybGRSZWdpb25cIjpcIlBha2lzdGFuXCJ9IiwiaXNfcHJlbWl1bSI6ZmFsc2V9; jwt_s=L26O-xFHQF15UgHPxOQnZlGGpYZfUCfLaM0vhXj3brOaZSIH8a3xygAZb6JdTLaIgFTSF8zmzupZeV8QM7OJg15QZbm5JAF-J68Kbmtkoroz39iXZ33Jpm5RcyMFEwOJbUnuhOvonUfgKpGLdwYeTLCHjESrV3fHcH7AgHT86dCXuFiGAdGCY_ivlvRIN42ytIjURa9DS5z_0x8L2HakGlmAO5WbLhxcJMapzk8x81g04NF-LWQD_W9q4UKOK98z7A3g4Gd0FGUB1okwDgRyCr9bxTq-ZEUgcep6x4bUaa1tKVYTCUutowOcKaD4iox4kQg-BeFbV_HUB7U-zjfaq6QKilJbqXvKPzfh67w63wh115LdqK6CTIdZEBoUNg_PutjnH_OxR8aIl68LHj_lxOsPmXK-mOjjfxu2VLJz-Dgr4FG8eFxjJn-zHbZdExxGMQNfzwx8-oc-bAbl8KRKoeeABYGeHiwA4E31gs34jWjahiTIQIXRLH52pmT21x45LqhZBmheDqwmrMXY9LjOSKdiUA3SdtvYJl5LWl7kSvQZL-JFpGoSPNNNUXNkgHjEFmQJnxi6pNZyX5D7ApDbVbcue-gfL2lKn3JMrG8Q7Q7QOxwZa0ABVks5gLfcTiYhMxJ5cdrgWSfVSySedPjEqZq-7YaQBLG2nL_MMhL6-Fg; ssr_i18n=en; user_i18n=en; __Host-csrf=e6118a37-0812-4ed6-8b81-ed883bc76e03"
# }
#
# resp = requests.post(
#     "https://www.jobleads.com/api/v2/search/v2",
#     headers=headers,
#     cookies=cookies,
#     json=payload,             # use json= instead of data= for proper JSON encoding
#     impersonate="chrome124"   # pick a close browser fingerprint (you can change this)
# )
#
# print(resp.status_code)
# print(resp.text)

#
# from curl_cffi import requests
#
# body = """
# {"keywords":"python","location":"","country":"NLD","radius":0,"minSalary":40000,"maxSalary":-1,"initialSearchId":0,"refinedSearchId":0,"lastExecutedSearch":null,"searchFiltering":0,"featuredJobs":"","origin":1,"savedSearchId":null,"startIndex":0,"limit":25,"filters":{}}
# """
#
# headers = {
#     "accept": "application/json, text/plain, */*",
#     "accept-language": "en-US,en;q=0.9",
#     "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3Njk1MjQ4NTMsImV4cCI6MTgwMTA2MDg1Mywicm9sZXMiOlsiUFVCTElDX0FDQ0VTUyJdLCJ1c2VybmFtZSI6IiIsImlkIjpudWxsLCJtZDVVc2VyIjpudWxsLCJ1YyI6bnVsbCwibG9jYWxpemF0aW9uIjoie1wibG9jYWxlXCI6XCJlbl9QS1wiLFwid29ybGRSZWdpb25cIjpcIlBha2lzdGFuXCJ9In0.sFr_bzBeCKhUzTFATL6LKgNJ1AH-_1biXUXbsKbtu054WL38NppcmreYjiUgzSCEoF0RWbmDmmpZZWPQzxjd06sHg8029qVI3zM8AT_1iA-SW8yTW50kRz-EI09nTKEzvk4AvJ1PHTUCM26jnNDLSIj1VgTZXIrIrGHg0LPv4VBhM_yfS9_htc-OyYjrPhXcZ78HsfeEh1BFVEwxQL3FXPO_Uupzzy0jKh3Nnn4X7xHWueXxTOl5us4rHam0hZT4gozhkWzhETmOl5sTZRdmWvYP2XnzakRo1CyPGhvwwEGYQSrZE3nvcvYeJL64cfWu1_3YhMwHiIB3PAc9sHSfP3SAJjf_YMBUZST3z6yum1UtyY040I7zJKra-mguQ4kPsZ6hUlJj52Xr9JuSvN8x-JAJZD4s8y2QJLgcklY75qoynd3DkZpDyHR1CYsVfZXt9Y6F5Uw7z670qj-AxCjaK2fAphMyPX7czeL84gmYneBatK1X8GCL_Xk7kzACWqrcbjB7h_ObuHWCfKAtpO6-IClNqeDENtLb2gOT-pnpD5JyNFEhgK6YqJyc2BB47NHmhnRt4MPI-nNyNbDZOg1xWMuDujOlNrfiHOWBpRN8Wuw1JcWt1rfjA-J6OY_mAphBrT2c8tUPQk-V2dnVW8WpejsNQij-OFAJiPw4WYni4YM",
#     "baggage": "sentry-environment=production,sentry-release=jobleadsapp_ssr%3E%4025.37.0,sentry-public_key=9717970d89a541699aac026424d1a45f,sentry-trace_id=fc5be4613f20460faa701194d309df6c,sentry-sample_rate=0.005,sentry-sampled=false",
#     "cf-ipcountry": "PK",
#     "content-type": "application/json",
#     "origin": "https://www.jobleads.com",
#     "priority": "u=1, i",
#     "referer": "https://www.jobleads.com/search/jobs?keywords=python&location=&location_country=NLD&minSalary=40000&maxSalary=-1",
#     "sec-ch-ua": "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
#     "sec-ch-ua-mobile": "?0",
#     "sec-ch-ua-platform": "\"macOS\"",
#     "sec-fetch-dest": "empty",
#     "sec-fetch-mode": "cors",
#     "sec-fetch-site": "same-origin",
#     "sentry-trace": "fc5be4613f20460faa701194d309df6c-b31314d19a343cd6-0",
#     "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
#     "x-requested-with": "XMLHttpRequest",
# }
#
# cookies = {
#     "locale": "en_PK",
#     "jlst": "1f0ffaa5-4f50-6398-8660-0dd9927f615c",
#     "ssr_i18n": "en",
#     "user_i18n": "en",
#     "__Host-csrf": "6a9129bf-3c21-4f7c-9f9a-6e17d2ec4efb",
#     "__cf_bm": "FacaAKDQ35hEOgFl6Ne2AaCA18s77namBJClnxLt0gY-1770015721-1.0.1.1-YDjCxBOLRbxXqqYCTZH2BG8ZvdeDtzSgNN7YpzptcrTAgtqwkSx.885NT1rnRApJKuY4HXINilHg0gMGZ03jzbEeUPmEiCJDo.5fomPkpqg",
#     "prodsid": "j7p1po5pcascvi14nekmm6k5vd",
# }
#
# response = requests.post(
#     "https://www.jobleads.com/api/v2/search/v2",
#     headers=headers,
#     cookies=cookies,
#     data=body,
#     impersonate="chrome124"
# )
#
# print(response.status_code)
# print(response.text)


import base64
import json
import time
from curl_cffi import requests


def _jwt_payload(token: str) -> dict:
    """Decode JWT payload without verifying signature (for exp only)."""
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
    except Exception:
        return {}


def _looks_like_jwt(s: str) -> bool:
    return isinstance(s, str) and s.count(".") == 2 and len(s) > 50


class JobleadsClient:
    def __init__(self, email: str, password: str, impersonate="chrome124"):
        self.email = email
        self.password = password
        self.impersonate = impersonate
        self.s = requests.Session()

        self.token = None
        self.exp = 0  # epoch seconds


    def login_and_get_token(self) -> str:
        url = "https://www.jobleads.com/user/login/form"

        boundary = "----WebKitFormBoundary6QwfUhHc0phBQ9U6"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="email"\r\n\r\n{self.email}\r\n'
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="password"\r\n\r\n{self.password}\r\n'
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="autoLogin"\r\n\r\n0\r\n'
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="redirectBackUrl"\r\n\r\n/home\r\n'
            f"--{boundary}--\r\n"
        )

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://www.jobleads.com",
            "referer": "https://www.jobleads.com/",
            "user-agent": "Mozilla/5.0",
            "x-requested-with": "XMLHttpRequest",
            "content-type": f"multipart/form-data; boundary={boundary}",
        }

        r = self.s.post(
            url,
            headers=headers,
            data=body,
            impersonate=self.impersonate,
        )
        r.raise_for_status()

        # ✅ This is the JWT you need
        # token = self.s.cookies.get("jwt_hp")
        token = self.s.cookies.get("jwt_hp")

        # if isinstance(token, str) and token.count(".") >= 1:
        #     return token
        hp = self.s.cookies.get("jwt_hp")
        sig = self.s.cookies.get("jwt_s")

        if not hp or not sig:
            print("cookie keys:", list(self.s.cookies.keys()))
            raise RuntimeError("Login OK but jwt_hp/jwt_s missing")

        return f"{hp}.{sig}"

        print("cookie keys:", list(self.s.cookies.keys()))
        raise RuntimeError("Login OK but jwt_hp not found")

    def refresh_if_needed(self, skew_seconds=120):
        if not self.token or time.time() >= (self.exp - skew_seconds):
            new_token = self.login_and_get_token()
            payload = _jwt_payload(new_token)
            self.token = new_token
            self.exp = int(payload.get("exp", 0)) or 0

    def request(self, method: str, url: str, *, headers=None, retry=True, **kwargs):
        self.refresh_if_needed()

        hdrs = dict(headers or {})
        hdrs["authorization"] = f"Bearer {self.token}"

        resp = self.s.request(
            method,
            url,
            headers=hdrs,
            impersonate=self.impersonate,
            **kwargs
        )

        # If server says token invalid/expired, re-login once & retry
        if retry and resp.status_code in (401, 403):
            self.token = None
            self.exp = 0
            self.refresh_if_needed(skew_seconds=0)

            hdrs["authorization"] = f"Bearer {self.token}"
            resp = self.s.request(
                method,
                url,
                headers=hdrs,
                impersonate=self.impersonate,
                **kwargs
            )

        return resp


# -------------------------
# Example usage: Search API
# -------------------------
client = JobleadsClient(
    email="berapec475@ixunbo.com",
    password="Berapec475@ixunbo.com",
    impersonate="chrome124"
)

search_headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "origin": "https://www.jobleads.com",
    "referer": "https://www.jobleads.com/",
    "user-agent": "Mozilla/5.0",
    "x-requested-with": "XMLHttpRequest",
}

payload = {
    "keywords": "python",
    "location": "",
    "country": "NLD",
    "radius": 0,
    "minSalary": 40000,
    "maxSalary": -1,
    "initialSearchId": 0,
    "refinedSearchId": 0,
    "lastExecutedSearch": None,
    "searchFiltering": 0,
    "featuredJobs": "",
    "origin": 1,
    "savedSearchId": None,
    "startIndex": 0,
    "limit": 25,
    "filters":
            [
                {
                    "key": "location",
                    "operator": "eq",
                    "value": [
                        {
                            "alpha2Country": "NL",
                            "names": []
                        }
                    ]
                },
                {
                    "key": "minSalary",
                    "value": 40000,
                    "operator": "gte"
                },
                {
                    "key": "validFrom",
                    "value": 1769937615,
                    "operator": "gte"
                }
]
}


resp = client.request(
    "POST",
    "https://www.jobleads.com/api/v2/search/v2",
    headers=search_headers,
    json=payload
)

print(resp.status_code)
print(resp.text)