import pytest
<<<<<<< HEAD

from quipubase.qdoc import QuipuDocument, Status
=======
from quipubase.documents import QDocument, Status
>>>>>>> d9ce0b98a79c88603e7bd0370e77017f80998029


class Dog(QuipuDocument):
    name: str
    breed: str


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
def test_dog(name: str, breed: str):
    dog = Dog(name=name, breed=breed)
    res = dog.put_doc()
    assert isinstance(res, Status)
    assert res.key == dog.key
    dog_in_db = Dog.get_doc(key=dog.key)
    assert isinstance(dog_in_db, Dog)
    dogs = Dog.scan_docs(limit=10, offset=0)
    assert isinstance(dogs, list)
    assert isinstance(dogs[0], Dog)
    dogs_filtered = Dog.find_docs(limit=10, offset=0, name=name)
    assert isinstance(dogs_filtered, list)
    assert isinstance(dogs_filtered[0], Dog)
    res = dog.delete_doc(key=dog.key)
    assert isinstance(res, Status)
    assert Dog.exists(key=dog.key) is not True
    assert isinstance(Dog.get_doc(key=dog.key), Status)
