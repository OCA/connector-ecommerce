from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    old_rules = ["connector_ecommerce.excep_product_has_checkpoint"]
    openupgrade.delete_records_safely_by_xml_id(old_rules)
