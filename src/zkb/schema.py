from typing import List, Optional


class SchemaManager:
    def __init__(self, zkb) -> None:
        self.zkb = zkb

    def register_entity_type(self, type: str, attributes: List[str]) -> int:
        """
        Register a new entity type in the domain schema.

        Parameters
        ----------
        type : str
            The name of the entity type
        attributes : List[str]
            A list of attribute names for this entity type

        Returns
        -------
        int
            The ID of the newly registered entity type schema
        """
        schema_id = self.zkb.db.add_entity(
            "schema", f"{type}_schema", {"attributes": ",".join(attributes)}
        )
        return schema_id

    def get_entity_schema(self, type: str) -> Optional[List[str]]:
        """
        Get the schema (list of attributes) for a given entity type.

        Parameters
        ----------
        type : str
            The name of the entity type

        Returns
        -------
        Optional[List[str]]
            The list of attributes for the entity type, or None if not found
        """
        schemas = self.zkb.db.get_entities("schema", {"name": f"{type}_schema"})
        if schemas:
            schema_id = schemas[0][0]
            attributes = self.zkb.db.get_attribute_value(schema_id, "attributes")
            return attributes.split(",")
        return None

    def list_entity_types(self) -> List[str]:
        """
        List all registered entity types.

        Returns
        -------
        List[str]
            A list of all registered entity type names
        """
        schemas = self.zkb.db.get_entities("schema")
        return [schema[1].replace("_schema", "") for schema in schemas]
