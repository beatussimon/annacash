"""
Management command to populate AnnaCash with realistic Tanzanian sample data.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Populate database with realistic Tanzanian sample data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Clear existing data
        self.clear_data()
        
        # Create users
        users = self.create_users()
        self.stdout.write(f'Created {len(users)} users')
        
        # Create config data
        banks = self.create_banks()
        networks = self.create_networks()
        self.stdout.write(f'Created {len(banks)} banks and {len(networks)} networks')
        
        # Create wakala businesses
        wakalas = self.create_wakalas(users)
        self.stdout.write(f'Created {len(wakalas)} wakala businesses')
        
        # Create mchezo groups
        groups = self.create_mchezo_groups(users)
        self.stdout.write(f'Created {len(groups)} mchezo groups')
        
        # Create sample transactions
        self.create_transactions(wakalas, users)
        self.stdout.write('Created sample transactions')
        
        # Create audit logs
        self.create_audit_logs(users)
        self.stdout.write('Created audit logs')
        
        self.stdout.write(self.style.SUCCESS('Sample data populated successfully!'))
        
        # Print summary
        self.print_summary(users, wakalas, groups)

    def clear_data(self):
        """Clear existing data."""
        from accounts.models import User, UserProfile
        from config.models import Bank, Network, Currency, FeeRule, CommissionRule
        from wakala.models import Wakala, FinancialDay, Transaction
        from mchezo.models import Group, Membership, Cycle, Contribution, Payout
        from core.models import AuditLog, WakalaRole, MchezoRole
        
        AuditLog.objects.all().delete()
        WakalaRole.objects.all().delete()
        MchezoRole.objects.all().delete()
        Payout.objects.all().delete()
        Contribution.objects.all().delete()
        Cycle.objects.all().delete()
        Membership.objects.all().delete()
        Group.objects.all().delete()
        Transaction.objects.all().delete()
        FinancialDay.objects.all().delete()
        Wakala.objects.all().delete()
        CommissionRule.objects.all().delete()
        FeeRule.objects.all().delete()
        Network.objects.all().delete()
        Bank.objects.all().delete()
        Currency.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        
    def create_users(self):
        """Create realistic Tanzanian users."""
        from accounts.models import User, UserProfile
        
        tanzanian_names = [
            ('John', 'Mwenda', 'john.mwenda@gmail.com', '0751234567'),
            ('Maria', 'Komba', 'maria.komba@gmail.com', '0752345678'),
            ('Peter', 'Mushi', 'peter.mushi@gmail.com', '0753456789'),
            ('Grace', 'Mrema', 'grace.mrema@gmail.com', '0754567890'),
            ('James', 'Lema', 'james.lema@gmail.com', '0755678901'),
            ('Anna', 'Maro', 'anna.maro@gmail.com', '0756789012'),
            ('David', 'Mtei', 'david.mtei@gmail.com', '0757890123'),
            ('Sarah', 'Mongella', 'sarah.mongella@gmail.com', '0758901234'),
            ('Michael', 'Kilo', 'michael.kilo@gmail.com', '0759012345'),
            ('Elizabeth', 'Mamba', 'elizabeth.mamba@gmail.com', '0760123456'),
            ('Robert', 'Ndess', 'robert.ndess@gmail.com', '0761234567'),
            ('Jennifer', 'Mwalimu', 'jennifer.mwalimu@gmail.com', '0762345678'),
            ('William', 'Kivuyo', 'william.kivuyo@gmail.com', '0763456789'),
            ('Linda', 'Msuya', 'linda.msuya@gmail.com', '0764567890'),
            ('Charles', 'Mungure', 'charles.mungure@gmail.com', '0765678901'),
            ('Patricia', 'Mhina', 'patricia.mhina@gmail.com', '0766789012'),
            ('Joseph', 'Mlwange', 'joseph.mlwange@gmail.com', '0767890123'),
            ('Barbara', 'Mkwizu', 'barbara.mkwizu@gmail.com', '0768901234'),
            ('Thomas', 'Msyani', 'thomas.msyani@gmail.com', '0769012345'),
            ('Susan', 'Mlinga', 'susan.mlinga@gmail.com', '0770123456'),
        ]
        
        regions = ['Dar es Salaam', 'Arusha', 'Dodoma', 'Mwanza', 'Tanga', 'Mbeya', 'Morogoro']
        districts = {
            'Dar es Salaam': ['Ilala', 'Kinondoni', 'Temeke', 'Ubungo', 'Kigamboni'],
            'Arusha': ['Arusha City', 'Meru', 'Arumeru'],
            'Dodoma': ['Dodoma Urban', 'Chamwino', 'Kondoa'],
            'Mwanza': ['Ilemela', 'Nyamagana', 'Mwanza Urban'],
            'Tanga': ['Tanga Urban', 'Muheza', 'Pangani'],
            'Mbeya': ['Mbeya Urban', 'Mbeya Rural', 'Rungwe'],
            'Morogoro': ['Morogoro Urban', 'Mvomero', 'Kilombero'],
        }
        
        users = []
        for first_name, last_name, email, phone in tanzanian_names:
            region = random.choice(regions)
            district = random.choice(districts[region])
            
            user = User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone,
                password='password123',
                region=region,
                district=district,
                national_id=str(random.randint(10000000, 99999999)),
            )
            
            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'default_currency': 'TZS',
                    'language': 'sw',
                    'sms_notifications': True,
                    'email_notifications': True,
                }
            )
            users.append(user)
        
        # Create a superuser
        superuser, _ = User.objects.get_or_create(
            email='admin@annacash.com',
            defaults={
                'first_name': 'System',
                'last_name': 'Admin',
            }
        )
        if superuser.pk:
            superuser.set_password('admin123')
            superuser.save()
        else:
            superuser.set_password('admin123')
        
        UserProfile.objects.get_or_create(user=superuser, defaults={
            'default_currency': 'TZS',
            'language': 'sw',
        })
        
        return users

    def create_banks(self):
        """Create Tanzanian banks."""
        from config.models import Bank
        
        banks = [
            ('CRDB', 'CRDB Bank Plc', 'TANZCRDB'),
            ('NMB', 'National Microfinance Bank', 'TANNMB'),
            ('NBC', 'National Bank of Commerce', 'TANNBC'),
            ('EXIM', 'Exim Bank Tanzania', 'TANEXIM'),
            ('ABC', 'ABC Bank Tanzania', 'TANABC'),
            ('I&M', 'I&M Bank Tanzania', 'TANIM'),
            ('Stanbic', 'Stanbic Bank Tanzania', 'TANSTB'),
            ('EcoBank', 'EcoBank Tanzania', 'TANECO'),
            ('KCB', 'Kenya Commercial Bank Tanzania', 'TANKCB'),
            ('DTB', 'Diamond Trust Bank Tanzania', 'TANDTB'),
        ]
        
        bank_objects = []
        for code, name, swift in banks:
            bank, _ = Bank.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'swift_code': swift,
                    'is_active': True,
                }
            )
            bank_objects.append(bank)
        
        return bank_objects

    def create_networks(self):
        """Create mobile money networks."""
        from config.models import Network
        
        networks = [
            ('M-PESA', '*150*00#', 'M-PESA Mobile Money'),
            ('TIGO PESA', '*150*01#', 'TIGO PESA'),
            ('AIRTEL MONEY', '*150*60#', 'Airtel Money'),
            ('HALOPESA', '*150*88#', 'HALO PESA'),
            ('EZY PESA', '*150*32#', 'EZY PESA'),
        ]
        
        network_objects = []
        for code, ussd, name in networks:
            network, _ = Network.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'ussd_code': ussd,
                    'is_active': True,
                }
            )
            network_objects.append(network)
        
        return network_objects

    def create_wakalas(self, users):
        """Create wakala businesses."""
        from wakala.models import Wakala
        from core.models import WakalaRole
        
        wakala_data = [
            ('Mwanzo General Shop', 'General Retail', users[0]),
            ('Mwinyi Mobile Services', 'Mobile Money Agent', users[1]),
            ('Tausi Electronics', 'Electronics', users[2]),
            ('Jamaa Supermarket', 'Supermarket', users[3]),
            ('Kaskazini POS', 'Point of Sale', users[4]),
            ('Baraka Airtime Shop', 'Airtime & Bills', users[5]),
            ('Duka la Michezo', 'Sports Goods', users[6]),
            ('Mama Samia Grocery', 'Grocery Store', users[7]),
            ('Quick Cash Agency', 'Financial Services', users[8]),
            ('Tanzania Tech Hub', 'Electronics & Services', users[9]),
        ]
        
        wakala_regions = ['Dar es Salaam', 'Arusha', 'Dodoma', 'Mwanza', 'Tanga']
        
        wakalas = []
        for name, biz_type, owner in wakala_data:
            wakala = Wakala(
                name=name,
                business_type=biz_type,
                owner=owner,
                phone_number=owner.phone_number,
                email=f'{name.lower().replace(" ", ".")}@gmail.com',
                address=f'{random.randint(1, 999)} {random.choice(["Kenyatta", "Julius Nyerere", "Mlimani", "Samora", "Moses"])} Street',
                region=random.choice(wakala_regions),
                district=random.choice(['Ilala', 'Kinondoni', 'Temeke', 'Arusha City', 'Dodoma Urban']),
                is_active=True,
                created_by=owner,
                original_recorder=owner,
            )
            wakala.save()
            
            # Create owner role
            WakalaRole.objects.create(
                wakala=wakala,
                user=owner,
                role='owner',
                granted_by=owner,
            )
            
            wakalas.append(wakala)
        
        return wakalas

    def create_mchezo_groups(self, users):
        """Create mchezo (ROSCA) groups."""
        from mchezo.models import Group, Membership, Cycle
        from core.models import MchezoRole
        
        group_names = [
            ('Vijana Savings Group', 50000, 'weekly'),
            ('Mama na Baba Circle', 100000, 'weekly'),
            ('Youth Entrepreneurs', 25000, 'weekly'),
            ('Village Heroes', 75000, 'weekly'),
            ('Women Empowerment Group', 30000, 'weekly'),
            ('Business Owners Circle', 150000, 'monthly'),
            ('Farmers Savings', 20000, 'weekly'),
            ('Teachers Mutual Aid', 50000, 'biweekly'),
            ('Market Vendors Group', 25000, 'daily'),
            ('Community Heroes', 100000, 'weekly'),
        ]
        
        tanzanian_cities = ['Dar es Salaam', 'Arusha', 'Dodoma', 'Mwanza', 'Mbeya', 'Tanga', 'Morogoro']
        
        groups = []
        for name, amount, frequency in group_names:
            admin = random.choice(users)
            
            group = Group(
                name=name,
                description='A community savings and loan group focused on mutual financial empowerment.',
                contribution_amount=amount,
                contribution_frequency=frequency,
                max_members=random.randint(8, 15),
                contribution_day=random.randint(1, 7),
                is_active=True,
                is_open=True,
                payout_order_method='random',
                created_by=admin,
                original_recorder=admin,
            )
            group.save()
            
            # Create admin role
            MchezoRole.objects.create(
                group=group,
                user=admin,
                role='admin',
                granted_by=admin,
            )
            
            # Add random members
            num_members = random.randint(5, 12)
            selected_users = random.sample(users, min(num_members, len(users)))
            selected_users.append(admin)  # Ensure admin is a member
            
            for i, member in enumerate(selected_users):
                membership, created = Membership.objects.get_or_create(
                    group=group,
                    user=member,
                    defaults={
                        'status': 'active',
                        'payout_order': i + 1,
                        'phone_number': member.phone_number,
                        'created_by': admin,
                        'original_recorder': admin,
                    }
                )
            
            # Create an active cycle
            start_date = date.today() - timedelta(days=random.randint(1, 30))
            cycle = Cycle(
                group=group,
                cycle_number=1,
                status='active',
                start_date=start_date,
                created_by=admin,
                original_recorder=admin,
            )
            cycle.save()
            
            groups.append(group)
        
        return groups

    def create_transactions(self, wakalas, users):
        """Create sample transactions."""
        from wakala.models import Wakala, FinancialDay, Transaction
        from config.models import Network, Bank
        
        networks = list(Network.objects.all())
        banks = list(Bank.objects.all())
        
        transaction_types = ['deposit', 'withdrawal', 'transfer_in', 'transfer_out', 'fee']
        payment_methods = ['Cash', 'Mobile Money', 'Bank Transfer', 'Cheque']
        
        for wakala in wakalas:
            # Create a financial day
            today = date.today()
            yesterday = today - timedelta(days=1)
            
            # Create open financial day for today
            day = FinancialDay.objects.create(
                wakala=wakala,
                date=today,
                status='open',
                opening_balance=random.randint(100000, 500000),
                opened_by=wakala.owner,
            )
            
            # Create some transactions
            num_transactions = random.randint(5, 20)
            for _ in range(num_transactions):
                tx_type = random.choice(transaction_types)
                amount = random.randint(5000, 500000)
                
                network = random.choice(networks) if random.random() > 0.5 else None
                bank = random.choice(banks) if random.random() > 0.7 else None
                
                Transaction.objects.create(
                    wakala=wakala,
                    financial_day=day,
                    transaction_type=tx_type,
                    amount=amount,
                    currency='TZS',
                    customer_name=f'{random.choice(["John", "Mary", "Peter", "Anna", "James", "Grace"])} {random.choice(["Mwenda", "Komba", "Mushi", "Mrema", "Lema", "Maro"])}',
                    customer_phone=f'075{random.randint(1000000, 9999999)}',
                    customer_reference=f'TXN{random.randint(100000, 999999)}',
                    payment_method=random.choice(payment_methods),
                    network=network,
                    bank=bank,
                    status='completed',
                    description=f'{tx_type.title()} transaction',
                )
            
            # Create some historical days
            for i in range(3):
                hist_date = yesterday - timedelta(days=i + 1)
                opening_bal = random.randint(100000, 500000)
                closing_bal = opening_bal + random.randint(-50000, 100000)
                
                hist_day = FinancialDay.objects.create(
                    wakala=wakala,
                    date=hist_date,
                    status='closed',
                    opening_balance=opening_bal,
                    closing_balance=closing_bal,
                    computed_closing_balance=closing_bal,
                    discrepancy=0,
                    opened_by=wakala.owner,
                    closed_by=wakala.owner,
                )

    def create_audit_logs(self, users):
        """Create sample audit logs."""
        from core.models import AuditLog
        from django.contrib.contenttypes.models import ContentType
        from accounts.models import User
        from wakala.models import Wakala
        from mchezo.models import Group
        
        actions = ['login', 'create', 'update', 'view', 'open_day', 'close_day', 'record_transaction']
        
        wakalas = list(Wakala.objects.all())
        groups = list(Group.objects.all())
        
        # Create some audit logs for the past week
        for i in range(50):
            user = random.choice(users)
            action = random.choice(actions)
            
            if 'transaction' in action or 'day' in action:
                obj = random.choice(wakalas)
                content_type = ContentType.objects.get_for_model(Wakala)
            else:
                obj = random.choice(groups) if groups else None
                content_type = ContentType.objects.get_for_model(Group) if obj else None
            
            AuditLog.objects.create(
                user=user,
                action=action,
                content_type=content_type,
                object_id=str(obj.id) if obj else None,
                description=f'{user.get_full_name()} performed {action}',
                ip_address=f'197.250.{random.randint(1, 255)}.{random.randint(1, 255)}',
            )

    def print_summary(self, users, wakalas, groups):
        """Print summary of created data."""
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('SAMPLE DATA SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(f'Users: {len(users)}')
        self.stdout.write(f'Wakala Businesses: {len(wakalas)}')
        self.stdout.write(f'Mchezo Groups: {len(groups)}')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Superuser Login:'))
        self.stdout.write(self.style.SUCCESS('  Email: admin@annacash.com'))
        self.stdout.write(self.style.SUCCESS('  Password: admin123'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
