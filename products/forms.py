from django import forms
from .models import Category, Product, ProductImage,Review
from django.forms import inlineformset_factory
from .models import Category, Product, ProductImage, Review, ProductColor



class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'is_listed']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Category name',
                'class': 'admin-form-input'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Category description (optional)',
                'class': 'admin-form-input',
                'rows': 4
            }),
            'is_listed': forms.CheckboxInput(attrs={
                'class': 'admin-form-checkbox'
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("Category name cannot be empty.")

        # Check for duplicate name (case-insensitive)
        # Exclude current instance when editing
        qs = Category.objects.filter(
            name__iexact=name,
            is_deleted=False
        )
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A category with this name already exists.")
        return name

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description',
            'price', 'discount_price', 'stock',
            'brand', 'is_listed'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'admin-form-input'}),
            'name': forms.TextInput(attrs={
                'placeholder': 'Product name',
                'class': 'admin-form-input'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Product description',
                'class': 'admin-form-input',
                'rows': 4
            }),
            'price': forms.NumberInput(attrs={
                'placeholder': '0.00',
                'class': 'admin-form-input',
                'step': '0.01'
            }),
            'discount_price': forms.NumberInput(attrs={
                'placeholder': '0.00 (optional)',
                'class': 'admin-form-input',
                'step': '0.01'
            }),
            'stock': forms.NumberInput(attrs={
                'placeholder': '0',
                'class': 'admin-form-input'
            }),
            'brand': forms.TextInput(attrs={
                'placeholder': 'Brand name (optional)',
                'class': 'admin-form-input'
            }),
            'is_listed': forms.CheckboxInput(attrs={
                'class': 'admin-form-checkbox'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show non-deleted categories
        self.fields['category'].queryset = Category.objects.filter(
            is_deleted=False,
            is_listed=True
        )
        self.fields['category'].empty_label = "Select a category"

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price <= 0:
            raise forms.ValidationError("Price must be greater than zero.")
        return price

    def clean_discount_price(self):
        discount_price = self.cleaned_data.get('discount_price')
        if discount_price and discount_price <= 0:
            raise forms.ValidationError("Discount price must be greater than zero.")
        return discount_price

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        discount_price = cleaned_data.get('discount_price')
        if price and discount_price:
            if discount_price >= price:
                self.add_error(
                    'discount_price',
                    "Discount price must be less than regular price."
                )
        return cleaned_data



class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(attrs={'class': 'star-radio'}),
            'comment': forms.Textarea(attrs={
                'placeholder': 'Share your experience with this product...',
                'class': 'form-input',
                'rows': 4,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].empty_label = None  # removes the blank "---" option
        self.fields['rating'].choices = [
            (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')
        ]  
class ProductColorForm(forms.ModelForm):
    class Meta:
        model = ProductColor
        fields = ['name', 'hex_code', 'stock']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Color name (e.g. Red)',
                'class': 'admin-form-input'
            }),
            'hex_code': forms.TextInput(attrs={
                'type': 'color',
                'class': 'admin-color-picker',
            }),
            'stock': forms.NumberInput(attrs={
                'placeholder': '0',
                'class': 'admin-form-input',
                'min': '0'
            }),
        }

    def has_changed(self):
        """
        Return False for completely empty extra forms.
        This prevents validation errors on blank color rows.
        """
        if not self.instance.pk:
            # New form — only validate if name is filled
            name = self.data.get(self.add_prefix('name'), '').strip()
            if not name:
                return False
        return super().has_changed()
        
# Inline formset — manage multiple colors inside the product form
ProductColorFormSet = inlineformset_factory(
    Product,
    ProductColor,
    form=ProductColorForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)        