import pytest

from quipubase.qdoc import QuipuDocument, Status


class Dog(QuipuDocument):
    name: str
    breed: str


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name, breed",
    [
        ("Fido", "Golden Retriever"),
        ("Rex", "German Shepherd"),
        ("Buddy", "Labrador"),
        ("Max", "Poodle"),
        ("Charlie", "Bulldog"),
        ("Jack", "Beagle"),
        ("Cooper", "Pomeranian"),
        ("Rocky", "Rottweiler"),
        ("Bear", "Siberian Husky"),
        ("Duke", "Dalmatian"),
        ("Tucker", "Doberman"),
        ("Oliver", "Boxer"),
        ("Milo", "Chihuahua"),
        ("Teddy", "Pug"),
        ("Winston", "Shih Tzu"),
        ("Louie", "Yorkshire Terrier"),
        ("Murphy", "Miniature Schnauzer"),
        ("Bentley", "Cavalier King Charles Spaniel"),
        ("Zeus", "Jack Russell Terrier"),
        ("Cody", "Australian Shepherd"),
    ],
)
async def test_dog(name: str, breed: str):
    dog = Dog(name=name, breed=breed)
    res = await dog.put_doc()
    assert isinstance(res, Dog)
    assert res.key == dog.key
    dog_in_db = await Dog.get_doc(key=dog.key)
    assert isinstance(dog_in_db, Dog)
    dogs_filtered = await Dog.find_docs(limit=10, offset=0, name=name)
    assert isinstance(dogs_filtered, list)
    assert isinstance(dogs_filtered[0], Dog)
    res = await dog.delete_doc(key=dog.key)
    assert isinstance(res, Status)
