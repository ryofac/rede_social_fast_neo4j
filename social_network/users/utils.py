from social_network.users.models import User


async def get_user_with_posts_by_id(uuid: str):
    user = await User.find_one({"uuid": uuid})
