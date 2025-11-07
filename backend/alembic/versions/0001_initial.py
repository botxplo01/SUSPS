from alembic import op
import sqlalchemy as sa
from geoalchemy2.types import Geometry

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable PostGIS
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # users
    op.create_table(
        "users",
        sa.Column("user_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(length=50), nullable=False, unique=True),
        sa.Column("email", sa.String(length=100), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # urban_areas
    op.create_table(
        "urban_areas",
        sa.Column("area_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("area_type", sa.Text(), nullable=False),
        sa.Column(
            "geometry",
            Geometry(geometry_type="MULTIPOLYGON", srid=4326),
            nullable=False,
        ),
        sa.CheckConstraint(
            "area_type in ('residential','commercial','industrial','mixed')",
            name="ck_area_type",
        ),
    )
    op.create_index(
        "urban_areas_geom_gix", "urban_areas", ["geometry"], postgresql_using="gist"
    )

    # demographics
    op.create_table(
        "demographics",
        sa.Column("demo_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("region_name", sa.String(length=100), nullable=False),
        sa.Column("population", sa.Integer(), nullable=False),
        sa.Column(
            "age_distribution",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "gender_distribution",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("census_year", sa.SmallInteger(), nullable=False),
        sa.Column("area_id", sa.BigInteger(), sa.ForeignKey("urban_areas.area_id")),
    )

    # mobility_transport
    op.create_table(
        "mobility_transport",
        sa.Column(
            "transport_id", sa.BigInteger(), primary_key=True, autoincrement=True
        ),
        sa.Column("area_id", sa.BigInteger(), sa.ForeignKey("urban_areas.area_id")),
        sa.Column("mode", sa.Text(), nullable=False),
        sa.Column(
            "route_info",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("average_speed_kmh", sa.Float(), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.CheckConstraint("mode in ('bus','matatu','train','road')", name="ck_mode"),
    )

    # energy_consumption
    op.create_table(
        "energy_consumption",
        sa.Column("energy_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), sa.ForeignKey("urban_areas.area_id")),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("predicted_demand", sa.Float(), nullable=True),
        sa.Column("actual_demand", sa.Float(), nullable=True),
    )
    op.create_index("energy_area_ts_idx", "energy_consumption", ["area_id", "ts"])

    # traffic_flow
    op.create_table(
        "traffic_flow",
        sa.Column("traffic_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), sa.ForeignKey("urban_areas.area_id")),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("predicted_volume", sa.Integer(), nullable=True),
        sa.Column("actual_volume", sa.Integer(), nullable=True),
        sa.Column("congestion_level", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "congestion_level in ('low','medium','high')", name="ck_congestion_level"
        ),
    )
    op.create_index("traffic_area_ts_idx", "traffic_flow", ["area_id", "ts"])

    # urban_growth_predictions
    op.create_table(
        "urban_growth_predictions",
        sa.Column("growth_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("area_id", sa.BigInteger(), sa.ForeignKey("urban_areas.area_id")),
        sa.Column("prediction_date", sa.Date(), nullable=False),
        sa.Column("predicted_population", sa.Integer(), nullable=True),
        sa.Column(
            "predicted_land_use",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    # simulation_runs
    op.create_table(
        "simulation_runs",
        sa.Column(
            "simulation_id", sa.BigInteger(), primary_key=True, autoincrement=True
        ),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.user_id")),
        sa.Column(
            "run_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "parameters",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "results",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "area_ids",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    # system_logs
    op.create_table(
        "system_logs",
        sa.Column("log_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "ts",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.user_id")),
        sa.Column("action", sa.Text(), nullable=True),
        sa.Column(
            "severity", sa.Text(), server_default=sa.text("'info'"), nullable=False
        ),
        sa.CheckConstraint(
            "severity in ('info','warning','error')", name="ck_severity"
        ),
    )


def downgrade() -> None:
    op.drop_table("system_logs")
    op.drop_table("simulation_runs")
    op.drop_table("urban_growth_predictions")
    op.drop_index("traffic_area_ts_idx", table_name="traffic_flow")
    op.drop_table("traffic_flow")
    op.drop_index("energy_area_ts_idx", table_name="energy_consumption")
    op.drop_table("energy_consumption")
    op.drop_table("mobility_transport")
    op.drop_table("demographics")
    op.drop_index("urban_areas_geom_gix", table_name="urban_areas")
    op.drop_table("urban_areas")
    op.drop_table("users")
