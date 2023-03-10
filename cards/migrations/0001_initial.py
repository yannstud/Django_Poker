# Generated by Django 4.1.4 on 2022-12-14 10:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Deck',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('suit', models.CharField(max_length=30)),
                ('value', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='GameTable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('state', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('Card1', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='one', to='cards.deck')),
                ('Card2', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='two', to='cards.deck')),
                ('Card3', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tree', to='cards.deck')),
                ('Card4', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fourth', to='cards.deck')),
                ('Card5', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='five', to='cards.deck')),
                ('GameTable', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cards.gametable')),
            ],
        ),
        migrations.AddField(
            model_name='deck',
            name='GameTable',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cards.gametable'),
        ),
    ]
