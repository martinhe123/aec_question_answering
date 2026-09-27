from schemas import AECCategory, ResourceLink


RESOURCE_MAP: dict[AECCategory, tuple[ResourceLink, ...]] = {
    AECCategory.CODES: (
        ResourceLink(title="ICC Digital Codes", url="https://codes.iccsafe.org/"),
        ResourceLink(
            title="NFPA Codes and Standards",
            url="https://www.nfpa.org/codes-and-standards",
        ),
        ResourceLink(
            title="ADA Accessibility Standards",
            url="https://www.access-board.gov/ada/",
        ),
    ),
    AECCategory.SAFETY: (
        ResourceLink(
            title="OSHA Construction",
            url="https://www.osha.gov/construction",
        ),
        ResourceLink(
            title="NIOSH Construction",
            url="https://www.cdc.gov/niosh/construction/",
        ),
        ResourceLink(title="CPWR", url="https://www.cpwr.com/"),
    ),
    AECCategory.ARCHITECTURE: (
        ResourceLink(
            title="AIA Resource Center",
            url="https://www.aia.org/resource-center",
        ),
        ResourceLink(
            title="Whole Building Design Guide",
            url="https://www.wbdg.org/",
        ),
        ResourceLink(
            title="GSA Design and Construction",
            url="https://www.gsa.gov/real-estate/design-and-construction",
        ),
    ),
    AECCategory.STRUCTURES: (
        ResourceLink(
            title="ASCE Codes and Standards",
            url="https://www.asce.org/publications-and-news/codes-and-standards",
        ),
        ResourceLink(
            title="NIST Buildings and Construction",
            url="https://www.nist.gov/buildings-and-construction",
        ),
        ResourceLink(
            title="FEMA Building Science",
            url="https://www.fema.gov/emergency-managers/risk-management/building-science",
        ),
    ),
    AECCategory.ENERGY: (
        ResourceLink(
            title="DOE Buildings Energy Efficiency",
            url="https://www.energy.gov/topics/buildings-energy-efficiency",
        ),
        ResourceLink(
            title="ENERGY STAR Buildings",
            url="https://www.energystar.gov/buildings",
        ),
        ResourceLink(
            title="NREL Buildings Research",
            url="https://www.nrel.gov/buildings/",
        ),
    ),
    AECCategory.BUILDING_SYSTEMS: (
        ResourceLink(
            title="ASHRAE Technical Resources",
            url="https://www.ashrae.org/technical-resources",
        ),
        ResourceLink(
            title="DOE Buildings Energy Efficiency",
            url="https://www.energy.gov/topics/buildings-energy-efficiency",
        ),
        ResourceLink(
            title="NFPA Codes and Standards",
            url="https://www.nfpa.org/codes-and-standards",
        ),
    ),
    AECCategory.CONSTRUCTION: (
        ResourceLink(
            title="Whole Building Design Guide",
            url="https://www.wbdg.org/",
        ),
        ResourceLink(
            title="Construction Management Association of America",
            url="https://www.cmaanet.org/",
        ),
        ResourceLink(
            title="Construction Specifications Institute",
            url="https://www.csiresources.org/",
        ),
    ),
    AECCategory.MATERIALS: (
        ResourceLink(
            title="NIST Buildings and Construction",
            url="https://www.nist.gov/buildings-and-construction",
        ),
        ResourceLink(
            title="USDA Forest Products Laboratory",
            url="https://www.fpl.fs.usda.gov/",
        ),
        ResourceLink(
            title="American Concrete Institute",
            url="https://www.concrete.org/",
        ),
    ),
    AECCategory.SUSTAINABILITY: (
        ResourceLink(
            title="EPA Green Building",
            url="https://www.epa.gov/smartgrowth/green-building",
        ),
        ResourceLink(
            title="U.S. Green Building Council",
            url="https://www.usgbc.org/",
        ),
        ResourceLink(
            title="DOE Buildings Energy Efficiency",
            url="https://www.energy.gov/topics/buildings-energy-efficiency",
        ),
    ),
    AECCategory.GENERAL_AEC: (
        ResourceLink(
            title="Whole Building Design Guide",
            url="https://www.wbdg.org/",
        ),
        ResourceLink(
            title="AIA Resource Center",
            url="https://www.aia.org/resource-center",
        ),
        ResourceLink(
            title="ASCE Codes and Standards",
            url="https://www.asce.org/publications-and-news/codes-and-standards",
        ),
    ),
}
