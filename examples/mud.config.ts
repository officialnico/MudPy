import { defineWorld } from "@latticexyz/world";

export default defineWorld({
  tables: {
    CraftingRecipe: {
      schema: {
        output: "uint256",
        outputQuantity: "uint256",
        xp: "uint256",
        exists: "bool",
        inputs: "uint256[]",
        quantities: "uint256[]",
      },
      key: ["output"],
    },
    ActiveStoves: {
        schema:  {
            itemId: "uint256",
            totalActiveStoves: "uint256",
        },
        key: ["itemId"]
    },
    StackableItem: {
        schema:  {
            base: "uint256",
            input: "uint256",
            stackable: "bool",
        },
        key: ["base", "input"]
    },
    ItemInfo: {
        schema:  {
          itemId: "uint256",
          nonRemovable: "bool",
          nonPlaceable: "bool",
          isTool: "bool",
          isTable: "bool",
          isChair: "bool",
          isRotatable: "bool",
          themeId: "uint256",
          itemCategory: "uint256",
          returnsItem: "uint256", //after consuming this item, it returns this item
        },
        key: ["itemId"]
    },
    Inventory: {
        schema: {
          landId: "uint256",
          item: "uint256",
          quantity: "uint256"
        },
        key: ["landId", "item"]
    },
   
    LandInfo: {
      schema: {
        landId: "uint256",
        limitX: "uint256",
        limitY: "uint256",
        activeTables: "uint256",
        activeStoves: "uint256",
        isInitialized: "bool",
        seed: "uint32",
        tokenBalance: "uint256",
        cumulativeXp: "uint256",
        lastLevelClaimed: "uint256",
        yBound: "uint256[]"
      },
      key: ["landId"],
    },
    LandItemCookingState:{
      schema: {
        landId: "uint256",
        x: "uint256",
        y: "uint256",
        z: "uint256",
        yieldShares: "uint256",
        collateral: "uint256",
        recipeId: "uint256",
        stoveId: "uint256",
      },
      key: ["landId", "x", "y", "z"],
    },
    LandTablesAndChairs:{
      schema: {
        landId: "uint256",
        x: "uint256",
        y: "uint256",
        chairsOfTables: "uint256[3]",
        tablesOfChairs: "uint256[3]",
      },
      key: ["landId", "x", "y"],
    },
    LandItem:{
      schema: {
        landId: "uint256",
        x: "uint256",
        y: "uint256",
        z: "uint256",
        itemId: "uint256",
        placementTime: "uint256",
        dynamicUnlockTimes: "uint256",
        dynamicTimeoutTimes: "uint256",
        isRotated: "bool",
      },
      key: ["landId", "x", "y", "z"],
    },
    LandPermissions: {
        schema: {
          owner: "address",
          landId: "uint256",
          operator: "address",
          isOperator: "bool",
        },
        key: ["owner", "landId", "operator"]
      },
    LandCell: {
      schema: {
        landId: "uint256",
        x: "uint256",
        y: "uint256",
        zItemCount: "uint16",
      },
      key: ["landId", "x", "y"],
    },
   ConfigAddresses: {
      schema: {
        vestingAddress: "address",
        softTokenAddress: "address",
        itemsAddress: "address",
        redistributorAddress: "address",
        landNFTsAddress: "address",
        softDestinationAddress: "address",
        perlinItemConfigAddress: "address",
        landTransformAddress: "address",
        landTablesAndChairsAddress: "address",
        landQuestTaskProgressUpdateAddress: "address",
        vrgdaAddress: "address"
      },
      key: []
    },
    CafeCosmosConfig: {
      schema: {
        cookingCost: "uint256",
        softCostPerSquare: "uint256",
        landNonce: "uint256",
        initialLimitX: "uint256",
        initialLimitY: "uint256",
        minStartingX: "uint256",
        minStartingY: "uint256",
        totalLandSlotsSold: "uint256",
        startTime: "uint256",
        defaultLandType: "uint256",
        seedMask: "uint160",
        globalBoosterId: "uint256",
        maxGroupIdNumber: "uint256",
        chunkSize: "uint256",
        maxLevel: "uint256",
        categoryMaxBoost: "uint256[7]",
        maxBoosts: "uint256[3]",
        startingItems: "uint256[]",
        startingItemsQuantities: "uint256[]",
      },
      key: []
    },
    TransformationCategories:{
      schema:{
        base: "uint256", 
        input: "uint256",
        categories: "uint256[]"
      },
      key: ["base", "input"]
    },
    Transformations: {
      schema: {
        base: "uint256", 
        input: "uint256",
        next: "uint256",
        yield: "uint256",
        inputNext: "uint256",
        yieldQuantity: "uint256",
        unlockTime: "uint256",
        timeout: "uint256",
        timeoutYield: "uint256",
        timeoutYieldQuantity: "uint256",
        timeoutNext: "uint256",
        isRecipe: "bool",
        isWaterCollection: "bool",
        xp: "uint256",
        exists: "bool",
      },
      key: ["base", "input"]
    },
    WaterController: {
        schema: {
          QUERY_SCHEMA: "bytes32",
          minDelta: "int256",
          maxDelta: "int256",
          SOURCE_CHAIN_ID: "uint64",
          numSamples: "uint256",
          blockInterval: "uint256",
          minYieldTime: "uint256",
          maxYieldTime: "uint256",
          endBlockSlippage: "uint256",
          lastTWAP: "uint256",
          waterYieldTime: "uint256",
          lastUpdate: "uint256",
        },
        key: []
      },
      LevelReward: {
        schema: {
          level: "uint256",
          cumulativeXp: "uint256",
          tokens: "uint256",
          items: "uint256[]"
        },
        key: ["level"]
      },
      ClaimedLevels: {
        schema: {
          level: "uint256",
          landId: "uint256",
          claimed: "bool"
        },
        key: ["level", "landId"]
      },
      Quests:{
        schema: {
          numberOfQuests: "uint256",
          numberOfQuestsGroups: "uint256",
          numberOfRewards: "uint256",
          activeQuestGroups: "uint256[]",
        },
        key: []
      },
      RewardCollection:{
        schema:{
          rewardType: "uint256",
          rewardIds: "uint256[]"
        },
        key: ["rewardType"]
      },
      QuestCollection:{
        schema:{
          questGroupType: "uint256",
          questIds: "uint256[]",
          previousQuestIds: "uint256[]",
        },
        key: ["questGroupType"]
      },
      Reward:{
        schema: {
          id: "uint256",
          itemId: "uint256",
          rewardType: "uint256",
          quantity: "uint256",
        },
        key: ["id"]
      },
      QuestGroup:{
        schema: {
          id: "uint256",
          startsAt: "uint256",
          expiresAt: "uint256",
          sequential: "bool",
          questGroupType: "uint256",
          questIds: "uint256[]",
          rewardIds: "uint256[]"
        },
        key: ["id"]
      },
      Quest:{
        schema: {
          id: "uint256",
          duration: "uint256",
          exists: "bool",
          questName: "string",
          rewardIds: "uint256[]",
          tasks: "bytes32[]",
        },
        key: ["id"]
      },
      QuestTask:{
        schema:{
          taskId: "bytes32",
          questId: "uint256",
          taskType: "uint256",
          key: "bytes32",
          quantity: "uint256",
          exists: "bool",
          name: "string",
          taskKeys: "bytes32[]",
        },
        key: ["taskId"]
        },
        LandQuestGroups:{
          schema:{
            landId: "uint256",
            activeQuestGroupIds: "uint256[]",
            questGroupIds: "uint256[]"
          },
          key: ["landId"]
        },
        LandQuestTaskProgress:{
          schema:{
            landId: "uint256",
            questGroupId: "uint256",
            questId: "uint256",
            taskType: "uint256",
            taskKey: "bytes32",
            taskProgress: "uint256",
            taskCompleted: "bool",
          },
          key: ["landId", "questGroupId", "questId", "taskType", "taskKey"]
        },
        LandQuestGroup:{
          schema:{
            landId: "uint256",
            questGroupId: "uint256",
            active: "bool",
            numberOfQuests: "uint256",
            numberOfCompletedQuests: "uint256",
            claimed: "bool",
            expiresAt: "uint256",
          },
          key: ["landId", "questGroupId"]
        },
        LandQuest:{
          schema:{
            landId: "uint256",
            questGroupId: "uint256",
            questId: "uint256",
            numberOfTasks: "uint256",
            numberOfCompletedTasks: "uint256",
            claimed: "bool",
            active: "bool",
            expiresAt: "uint256",
          },
          key: ["landId", "questGroupId", "questId"]
        },
        Catalogue:{
          schema:{
            catalogueId: "uint256",
            catalogueName: "string",
          },
          key: ["catalogueId"]
        },
        CatalogueItem:{
          schema:{
            catalogueId: "uint256",
            itemId: "uint256",
            price: "uint256",
            exists: "bool",
          },
          key: ["itemId"]
        },
        GuildExists:{
          schema:{
            guildId: "uint8",
            exists: "bool"
          },
          key: ["guildId"]
        },
        GuildInvitation:{
          schema:{
            landId: "uint256",
            guildId: "uint8",
            isInvited: "bool"
          },
          key: ["landId", "guildId"]
        },
        MarketplaceListings:{
          schema:{
            listingId: "uint256",
            owner: "uint256",
            itemId: "uint256",
            unitPrice: "uint256",
            quantity: "uint256",
            exists: "bool",
          },
          key: ["listingId"]
        },
        MarketplaceNonce:{
          schema:{
            nonce: "uint256",
            totalListings: "uint256"
          },
          key: []
        },
        GuildsNonce:{
          schema:{
            nonce: "uint256"
          },
          key: []
        },
        PlayerGuild:{
          schema:{
            landId: "uint256",
            isGuildAdmin: "bool",
            guildName: "string",
          },
          key: ["landId"]
        },
        PlayerTotalEarned:{
          schema:{
            landId: "uint256",
            totalEarned: "uint256",
          },
          key: ["landId"]
        },
        Vrgda:{ 
          schema:{
            targetPrice: "int256", 
            decayConstant: "int256", 
            perTimeUnit: "int256",
            startingTime: "int256",
            totalUnitsSold: "uint256"
          },
          key: []
        }
  },
});