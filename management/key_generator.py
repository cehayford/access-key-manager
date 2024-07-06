from secrets import token_urlsafe

def generate_key(length):
    return token_urlsafe(length)


generate_access_key = generate_key(32)
# print(key)