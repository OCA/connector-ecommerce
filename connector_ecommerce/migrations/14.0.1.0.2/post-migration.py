from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    xml_id = "connector_ecommerce.excep_parent_order_need_cancel"
    record = env.ref(xml_id, raise_if_not_found=False)
    if record:
        record.code = "if self.parent_need_cancel: failed = True"

    xml_id = "connector_ecommerce.excep_order_need_cancel"
    record = env.ref(xml_id, raise_if_not_found=False)
    if record:
        record.code = "if self.need_cancel: failed = True"
