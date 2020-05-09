from __future__ import print_function
import logging
import sys

from aerospike import client, exception, predicates as p


logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)


def add_customer(customer_id, phone_number, lifetime_value):
    key = ("test", "customers", customer_id)
    bins = {"phone_number": phone_number, "ltv": lifetime_value}
    client.put(key, bins)


def get_ltv_by_id(customer_id):
    key = ("test", "customers", customer_id)
    try:
        (key, meta, bins) = client.get(key)
        return bins.get("ltv")
    except exception.RecordNotFound:
        logging.error("Record with customer_id → {} was not found!".format(customer_id))


def get_ltv_by_phone(phone_number):
    query = client.query("test", "customers").select("phone_number", "ltv")
    query.where(p.equals("phone_number", phone_number))
    try:
        results = query.results()
    except exception.IndexNotFound:
        logging.error("There is no secondary index defined for 'phone_number'")
        return None
    if results:
        return results[0][2].get("ltv")
    logging.error("Record with phone_number → {} was not found!".format(phone_number))


logging.info("Testing local Aerospike connectivity")
# Configure the client
config = {"hosts": [("db", 3000)], "policies": {"timeout": 1000}}

# Create a client and connect it to the cluster
try:
    client = client(config).connect()
except:
    logging.error("failed to connect to the cluster with", config["hosts"])
    sys.exit(1)

logging.info("Local Aerospike works fine")

# Configure secondary index for phone_number
try:
    client.index_integer_create("test", "customers", "phone_number", "index_phone")
except exception.IndexFoundError:
    pass

logging.info("Starting some local tests")

logging.info("Adding dummy user (1000001, 999, 99), check ltv and remove him")
add_customer(1000001, 999, 99)
assert get_ltv_by_id(1000001) == 99
assert get_ltv_by_phone(999) == 99
client.remove(("test", "customers", 1000001))
logging.info("The check is completed!")

logging.info(
    "Testing with non-existed customer_id = 1000002 and non-existed phone number = 1"
)
assert get_ltv_by_id(1000002) == None
assert get_ltv_by_phone(1) == None
logging.info("The check is completed!")

logging.info("Local testing completed!")
