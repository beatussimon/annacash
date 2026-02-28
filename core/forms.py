"""
Core form utilities for ANNA platform.
"""

from django import forms


class FormStyleMixin:
    """
    Mixin to automatically apply ANNA design system classes to form fields.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_anna_styles()

    def apply_anna_styles(self):
        """Apply CSS classes to all fields."""
        for field_name, field in self.fields.items():
            # Handle standard inputs
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                existing_classes = field.widget.attrs.get("class", "")
                if "anna-form-input" not in existing_classes:
                    field.widget.attrs["class"] = f"{existing_classes} anna-form-input".strip()
            
            # Handle checkboxes
            elif isinstance(field.widget, forms.CheckboxInput):
                existing_classes = field.widget.attrs.get("class", "")
                if "anna-form-check-input" not in existing_classes:
                    field.widget.attrs["class"] = f"{existing_classes} anna-form-check-input".strip()
            
            # Add placeholders if missing
            if not field.widget.attrs.get("placeholder") and field.label:
                field.widget.attrs["placeholder"] = field.label
