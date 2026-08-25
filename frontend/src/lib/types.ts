export interface Project {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

export interface Attribute {
  id: number;
  name: string;
}

export interface AttributeGroup {
  id: number;
  name: string;
  attributes: Attribute[];
}

export interface PageSelections {
  page: number;
  attribute_ids: number[];
}